---
name: git-workflow
description: Handle git operations including worktree creation, conventional commits, branch naming, PR creation, PR reviews, and PR comment addressing. Use when the user asks to create a branch, commit changes, create a pull request, review a PR, address PR comments, or create a git worktree.
---

# Git Workflow

## Utility Scripts

Scripts in `scripts/` handle complex git/gh operations that are error-prone to reproduce inline. Execute them directly with `python` — do not regenerate their logic inline. All scripts are stdlib-only Python.

Scripts are referenced as `scripts/...` relative paths. If that doesn't resolve (e.g. working from a worktree or different directory), the scripts are bundled alongside this skill file — use its parent directory to construct the absolute path.

All GitHub interactions use the `gh` CLI exclusively (no MCP tools for git/GitHub operations).

| Script | Purpose |
| ------ | ------- |
| `scripts/gather_repo_state.py` | Repo state JSON: owner, repo, branch, base, staged, commits ahead |
| `scripts/fetch_pr_context.py <owner> <repo> <N> [--max-lines] [--max-file-lines] [--no-skip]` | PR metadata + filtered per-file diffs as JSON |
| `scripts/fetch_threads.py <owner> <repo> <N>` | Fetch unresolved PR threads (paginated GraphQL) |
| `scripts/submit_review.py <owner> <repo> <N> <event> <summary> [comments.json]` | Submit review with optional line comments |
| `scripts/create_worktree.py <branch> [base]` | Create worktree in `$GIT_WORKTREE_DIR` with `<repo>-<branch-slug>` naming |
| `scripts/validate_commit_msg.py <msg>` | Validate conventional commit + 50/72 rules |

## Worktrees

```bash
python scripts/create_worktree.py <branch-name> [base-ref]
```

- Requires `$GIT_WORKTREE_DIR` to be set in the shell environment
- Creates the base directory if it doesn't exist
- Validates branch doesn't already exist locally or on remote
- Directory naming: `<repo>-<branch-slug>` (`widget` + `feat/add-auth` -> `widget-feat-add-auth`)

## Conventions Quick Reference

Full specification in [conventions.md](conventions.md).

**Branch**: `<type>/<description>` — lowercase alphanumerics and hyphens only

**Commit**: `<type>[optional scope]: <description>` — imperative mood, max 50 char subject

**PR title**: Same as commit format, description lowercase after prefix

| Type | Branch Prefix | Commit Prefix |
| ---- | ------------- | ------------- |
| Feature | `feat/` | `feat:` |
| Bug fix | `fix/` | `fix:` |
| Hotfix | `hotfix/` | `fix:` |
| Release | `release/` | `chore:` |
| Chore | `chore/` | `chore:` |
| Docs | `docs/` | `docs:` |
| Refactor | `refactor/` | `refactor:` |
| Test | `test/` | `test:` |
| CI | `ci/` | `ci:` |
| Build | `build/` | `build:` |
| Perf | `perf/` | `perf:` |
| Style | `style/` | `style:` |

## Branch Creation

1. Analyze staged/unstaged changes (or ask for context if ambiguous)
2. Generate: `git checkout -b <type>/<description>`
3. Rules: lowercase, hyphens between words, no consecutive/leading/trailing hyphens

## Commits

1. Run `git diff --staged`. If nothing is staged, ask the user what to stage (or `git add` specific files based on context) before proceeding.
2. If intent unclear, ask for task description
3. Generate two options — concise and detailed:

```bash
git commit -m "<type>[scope]: <description>"

git commit -m "<type>[scope]: <description>" -m "<body explaining what and why>"
```

4. Validate before committing:

```bash
python scripts/validate_commit_msg.py "<message>"
```

For multi-line messages (body/footer), write to a temp file and use `--file`:

```bash
python scripts/validate_commit_msg.py --file /tmp/commit-msg.txt
```

Returns `{"valid": true/false, "errors": [...]}`. Fix any errors before executing the commit.

### 50/72 Rule

- **Subject**: max 50 chars, imperative mood, no trailing period, lowercase after prefix
- **Body**: wrap at 72 chars, explain WHAT and WHY (not HOW), separate from subject with blank line
- **Footer**: `Closes #123`, `BREAKING CHANGE: ...`

### Breaking Changes

Indicate with `!` after type/scope (`feat!:`, `feat(api)!:`) or `BREAKING CHANGE:` footer.

## PR Creation

1. Gather repo state, create branch/commit if needed.
2. Generate PR title from commit/branch following conventions.
3. **MANDATORY**: Locate and fill the `PULL_REQUEST_TEMPLATE.md` (check repo root `.github/` first, then skill-bundled template).
4. **NEVER** use the commit message as the PR body. Always fill all relevant sections of the template based on the changes.
5. Push and create the PR using `gh pr create --title "<title>" --body "<body>"`.

Full procedure in [pr-operations.md](pr-operations.md).

## PR Review

1. **Fetch Context**: Use `python scripts/fetch_pr_context.py <owner> <repo> <number>` to get metadata and diffs.
2. **Determine Focus**: Default to comprehensive (Correctness, Security, etc.) unless overridden by user.
3. **Analyze**: Review diffs against focus areas; skip noisy/generated files automatically.
4. **Build Review**: Draft summary and line comments (prefixed with `[critical]`, `[suggestion]`, or `[nit]`).
5. **Confirm & Submit**: Present the full review to the user for confirmation before submitting via `python scripts/submit_review.py`.

Full procedure in [pr-operations.md](pr-operations.md).

## Address PR Comments

1. **Fetch Threads**: Use `python scripts/fetch_threads.py <owner> <repo> <number>` to get unresolved, non-outdated threads.
2. **Checkout & Fix**: Switch to the PR branch and implement minimal changes addressing feedback.
3. **Commit & Push**: Group related fixes into logical commits; validate messages before pushing.
4. **Reply**: Post descriptive replies to each thread using `gh api` only after a successful push.

Full procedure in [pr-operations.md](pr-operations.md).
