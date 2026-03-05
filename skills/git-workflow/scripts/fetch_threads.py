#!/usr/bin/env python
"""Fetch unresolved, non-outdated PR review threads with automatic pagination.

Usage: python fetch_threads.py <owner> <repo> <pr_number>
Output: JSON array of threads grouped by file path, to stdout.
"""

import json
import subprocess
import sys
from itertools import groupby

QUERY = """
query($owner:String!, $repo:String!, $number:Int!, $after:String) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      reviewThreads(first:100, after:$after) {
        nodes {
          id
          isResolved
          isOutdated
          comments(first:100) {
            nodes {
              databaseId
              author { login }
              body
              path
              line
              startLine
              originalLine
            }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""


def gh_graphql(owner: str, repo: str, number: int, after: str | None = None) -> dict:
    cmd = [
        "gh",
        "api",
        "graphql",
        "-F",
        f"owner={owner}",
        "-F",
        f"repo={repo}",
        "-F",
        f"number={number}",
        "-f",
        f"query={QUERY}",
    ]
    if after:
        cmd += ["-F", f"after={after}"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def fetch_all_threads(owner: str, repo: str, number: int) -> list[dict]:
    threads: list[dict] = []
    cursor = None

    while True:
        data = gh_graphql(owner, repo, number, cursor)
        review_threads = data["data"]["repository"]["pullRequest"]["reviewThreads"]

        for node in review_threads["nodes"]:
            if not node["isResolved"] and not node["isOutdated"]:
                threads.append(node)

        page_info = review_threads["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

    return threads


def transform(threads: list[dict]) -> list[dict]:
    flat = []
    for t in threads:
        comments = [
            {
                "comment_id": c["databaseId"],
                "author": c["author"]["login"],
                "body": c["body"],
                "path": c["path"],
                "line": c["line"],
                "start_line": c["startLine"],
                "original_line": c["originalLine"],
            }
            for c in t["comments"]["nodes"]
        ]
        if not comments:
            continue
        flat.append({"thread_id": t["id"], "comments": comments})

    def key_fn(t):
        return t["comments"][0]["path"] or ""

    sorted_threads = sorted(flat, key=key_fn)
    return [
        {"path": path, "threads": list(group)}
        for path, group in groupby(sorted_threads, key=key_fn)
    ]


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: fetch_threads.py <owner> <repo> <pr_number>", file=sys.stderr)
        sys.exit(1)

    owner, repo, number = sys.argv[1], sys.argv[2], int(sys.argv[3])
    threads = fetch_all_threads(owner, repo, number)
    result = transform(threads)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
