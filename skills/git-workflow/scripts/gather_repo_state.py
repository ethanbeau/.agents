#!/usr/bin/env python
"""Gather repository state for PR creation workflow.

Usage: python scripts/gather_repo_state.py
Output: JSON object to stdout with all fields needed to determine the PR creation path.

Example output:
{
  "owner": "acme",
  "repo": "widget",
  "branch": "feature/add-auth",
  "base_branch": "develop",
  "on_base_branch": false,
  "has_staged": true,
  "staged_stat": "src/auth.py | 45 +++\n2 files changed",
  "commits_ahead": ["abc1234 feat(auth): add JWT validation"],
  "commits_ahead_count": 1
}
"""

import json
import subprocess
import sys
from urllib.parse import urlparse


def run(cmd: list[str], check: bool = True) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    return result.stdout.strip()


def parse_remote_url(url: str) -> tuple[str, str]:
    url = url.removesuffix(".git")
    if url.startswith("git@"):
        # git@github.com:owner/repo
        path = url.split(":", 1)[1]
    else:
        path = urlparse(url).path.lstrip("/")
    parts = path.split("/")
    return parts[0], parts[1]


def detect_base_branch() -> str:
    """Detect base branch: prefer develop (gitflow), else remote default, else main/master."""
    for ref in ("refs/heads/develop", "refs/remotes/origin/develop"):
        r = subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            return "develop"

    r = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        capture_output=True,
        text=True,
    )
    if r.returncode == 0:
        return r.stdout.strip().removeprefix("refs/remotes/origin/")

    for branch in ("main", "master"):
        r = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            return branch

    return "main"


def main() -> None:
    remote_url = run(["git", "remote", "get-url", "origin"])
    owner, repo = parse_remote_url(remote_url)
    branch = run(["git", "branch", "--show-current"])
    if not branch:
        print("ERROR: HEAD is detached (not on a branch)", file=sys.stderr)
        sys.exit(1)

    base_branch = detect_base_branch()
    on_base_branch = branch == base_branch

    run(["git", "fetch", "origin", base_branch, "--quiet"], check=False)

    staged_stat = run(["git", "diff", "--staged", "--stat"], check=False)
    has_staged = bool(staged_stat)

    commits_ahead_raw = run(
        ["git", "log", f"origin/{base_branch}..HEAD", "--oneline"],
        check=False,
    )
    commits_ahead = [line for line in commits_ahead_raw.splitlines() if line]

    state = {
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "base_branch": base_branch,
        "on_base_branch": on_base_branch,
        "has_staged": has_staged,
        "staged_stat": staged_stat,
        "commits_ahead": commits_ahead,
        "commits_ahead_count": len(commits_ahead),
    }
    json.dump(state, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
