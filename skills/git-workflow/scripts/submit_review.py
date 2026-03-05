#!/usr/bin/env python
"""Submit a PR review with optional line comments.

Usage: python submit_review.py <owner> <repo> <pr_number> <event> <summary> [comments_json_file]

event: COMMENT | REQUEST_CHANGES (never APPROVE)
comments_json_file: optional path to JSON array of {path, line, side, body}

Output: API response JSON to stdout.
"""

import json
import subprocess
import sys


def submit_with_comments(
    owner: str, repo: str, number: int, event: str, summary: str, comments: list[dict]
) -> None:
    payload = json.dumps({"event": event, "body": summary, "comments": comments})
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{owner}/{repo}/pulls/{number}/reviews",
            "--method",
            "POST",
            "--input",
            "-",
        ],
        input=payload,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    print(result.stdout)


def submit_simple(owner: str, repo: str, number: int, event: str, summary: str) -> None:
    flag = "--request-changes" if event == "REQUEST_CHANGES" else "--comment"
    result = subprocess.run(
        [
            "gh",
            "pr",
            "review",
            str(number),
            "--repo",
            f"{owner}/{repo}",
            flag,
            "--body",
            summary,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    print(result.stdout)


def main() -> None:
    if len(sys.argv) < 6:
        print(
            "Usage: submit_review.py <owner> <repo> <pr_number> <event> <summary> [comments.json]",
            file=sys.stderr,
        )
        sys.exit(1)

    owner, repo = sys.argv[1], sys.argv[2]
    number = int(sys.argv[3])
    event = sys.argv[4].upper()
    summary = sys.argv[5]
    comments_file = sys.argv[6] if len(sys.argv) > 6 else None

    if event == "APPROVE":
        print("ERROR: APPROVE is not permitted by review policy", file=sys.stderr)
        sys.exit(1)

    if event not in ("COMMENT", "REQUEST_CHANGES"):
        print(
            f"ERROR: Invalid event '{event}'. Use COMMENT or REQUEST_CHANGES",
            file=sys.stderr,
        )
        sys.exit(1)

    comments: list[dict] = []
    if comments_file:
        with open(comments_file) as f:
            comments = json.load(f)

    if comments:
        submit_with_comments(owner, repo, number, event, summary, comments)
    else:
        submit_simple(owner, repo, number, event, summary)


if __name__ == "__main__":
    main()
