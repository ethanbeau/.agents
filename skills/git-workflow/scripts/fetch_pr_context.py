#!/usr/bin/env python
"""Fetch PR metadata and diff for review or comment-addressing workflows.

Usage: python fetch_pr_context.py <owner> <repo> <pr_number> [options]

Options:
  --max-lines N       Total diff line budget across all files (default: 2000)
  --max-file-lines N  Per-file diff line cap (default: 300)
  --no-skip           Disable auto-skip of generated/noisy files

Output: JSON object to stdout with PR metadata and per-file diffs.
"""

import argparse
import fnmatch
import json
import re
import subprocess
import sys

SKIP_BASENAMES = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Pipfile.lock",
        "poetry.lock",
        "Cargo.lock",
        "Gemfile.lock",
        "composer.lock",
        "go.sum",
    }
)

SKIP_GLOBS = (
    "*.lock",
    "*.min.js",
    "*.min.css",
    "*.generated.*",
    "*_generated.*",
    "*.pb.go",
    "*_pb2.py",
    "*.snap",
)

SKIP_PATH_SEGMENTS = ("/vendor/", "/node_modules/", "/dist/", "/build/")

DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$")


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def should_skip(path: str) -> bool:
    basename = path.rsplit("/", 1)[-1] if "/" in path else path
    if basename in SKIP_BASENAMES:
        return True
    for glob in SKIP_GLOBS:
        if fnmatch.fnmatch(basename, glob):
            return True
    for segment in SKIP_PATH_SEGMENTS:
        if segment in f"/{path}/":
            return True
    return False


def is_binary_diff(chunk: str) -> bool:
    for line in chunk.split("\n", 10):
        if line.startswith("Binary files") or line.startswith("GIT binary patch"):
            return True
    return False


def parse_diff(raw_diff: str) -> list[dict]:
    """Split a unified diff into per-file chunks."""
    files: list[dict] = []
    current_path: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_path is not None:
            files.append({"path": current_path, "raw": "\n".join(current_lines)})

    for line in raw_diff.split("\n"):
        m = DIFF_HEADER_RE.match(line)
        if m:
            flush()
            current_path = m.group(2)
            current_lines = [line]
        else:
            current_lines.append(line)

    flush()
    return files


def build_churn_index(files_metadata: list[dict]) -> dict[str, int]:
    """Map file path -> additions+deletions from PR metadata."""
    index: dict[str, int] = {}
    for f in files_metadata:
        index[f["path"]] = f.get("additions", 0) + f.get("deletions", 0)
    return index


def process_diffs(
    raw_diff: str,
    files_metadata: list[dict],
    max_lines: int,
    max_file_lines: int,
    skip_enabled: bool,
) -> tuple[list[dict], list[str], dict]:
    parsed = parse_diff(raw_diff)
    churn = build_churn_index(files_metadata)

    skipped: list[str] = []
    candidates: list[dict] = []

    for entry in parsed:
        path = entry["path"]
        if skip_enabled and (should_skip(path) or is_binary_diff(entry["raw"])):
            skipped.append(path)
            continue
        candidates.append(entry)

    candidates.sort(key=lambda e: churn.get(e["path"], 0), reverse=True)

    diff_files: list[dict] = []
    budget_remaining = max_lines
    budget_exhausted = False
    truncated_count = 0

    for entry in candidates:
        if budget_remaining <= 0:
            budget_exhausted = True
            skipped.append(entry["path"])
            continue

        lines = entry["raw"].split("\n")
        was_truncated = False

        if len(lines) > max_file_lines:
            lines = lines[:max_file_lines]
            was_truncated = True

        if len(lines) > budget_remaining:
            lines = lines[:budget_remaining]
            was_truncated = True

        if was_truncated:
            truncated_count += 1

        budget_remaining -= len(lines)

        diff_files.append(
            {
                "path": entry["path"],
                "diff": "\n".join(lines),
                "truncated": was_truncated,
            }
        )

    stats = {
        "total_files": len(parsed),
        "shown_files": len(diff_files),
        "skipped_files": len(skipped),
        "truncated_files": truncated_count,
        "budget_exhausted": budget_exhausted,
    }

    return diff_files, skipped, stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("owner")
    parser.add_argument("repo")
    parser.add_argument("number")
    parser.add_argument("--max-lines", type=int, default=2000)
    parser.add_argument("--max-file-lines", type=int, default=300)
    parser.add_argument("--no-skip", action="store_true")
    args = parser.parse_args()

    repo_ref = f"{args.owner}/{args.repo}"

    metadata_raw = run(
        [
            "gh",
            "pr",
            "view",
            args.number,
            "--repo",
            repo_ref,
            "--json",
            "title,body,author,baseRefName,headRefName,files,additions,deletions",
        ]
    )
    metadata = json.loads(metadata_raw)

    raw_diff = run(["gh", "pr", "diff", args.number, "--repo", repo_ref])

    diff_files, skipped, stats = process_diffs(
        raw_diff,
        metadata.get("files", []),
        args.max_lines,
        args.max_file_lines,
        skip_enabled=not args.no_skip,
    )

    result = {
        "title": metadata["title"],
        "author": metadata["author"]["login"],
        "base": metadata["baseRefName"],
        "head": metadata["headRefName"],
        "additions": metadata["additions"],
        "deletions": metadata["deletions"],
        "files": metadata["files"],
        "body": metadata["body"],
        "diff_files": diff_files,
        "skipped_files": skipped,
        "diff_stats": stats,
    }
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
