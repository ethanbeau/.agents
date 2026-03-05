#!/usr/bin/env python
"""Create a git worktree using $GIT_WORKTREE_DIR.

Usage: python create_worktree.py <branch_name> [base_ref]

Directory naming: <repo>-<branch-slug> where the branch slug replaces / with -.
  e.g. repo "widget" + branch "feature/add-auth" -> "widget-feature-add-auth"

Requires $GIT_WORKTREE_DIR to be set.
Output: path to created worktree.
"""

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


def run(cmd: list[str], check: bool = True) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    return result.stdout.strip()


def repo_name() -> str:
    url = run(["git", "remote", "get-url", "origin"])
    url = url.removesuffix(".git")
    if url.startswith("git@"):
        path = url.split(":", 1)[1]
    else:
        path = urlparse(url).path.lstrip("/")
    return path.split("/")[-1]


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: create_worktree.py <branch_name> [base_ref]", file=sys.stderr)
        sys.exit(1)

    branch = sys.argv[1]
    base_ref = sys.argv[2] if len(sys.argv) > 2 else None

    worktree_dir = os.environ.get("GIT_WORKTREE_DIR")
    if not worktree_dir:
        print("ERROR: $GIT_WORKTREE_DIR is not set", file=sys.stderr)
        sys.exit(1)

    name = repo_name()
    slug = branch.replace("/", "-")
    worktree_path = Path(worktree_dir) / f"{name}-{slug}"

    if worktree_path.exists():
        print(f"ERROR: Worktree directory already exists: {worktree_path}", file=sys.stderr)
        sys.exit(1)

    r = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        print(f"ERROR: Branch '{branch}' already exists locally", file=sys.stderr)
        sys.exit(1)

    r = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch],
        capture_output=True, text=True,
    )
    if r.stdout.strip():
        print(f"ERROR: Branch '{branch}' already exists on remote", file=sys.stderr)
        sys.exit(1)

    Path(worktree_dir).mkdir(parents=True, exist_ok=True)

    cmd = ["git", "worktree", "add", str(worktree_path), "-b", branch]
    if base_ref:
        cmd.append(base_ref)

    subprocess.run(cmd, check=True)
    print(worktree_path)


if __name__ == "__main__":
    main()
