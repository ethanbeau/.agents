# PR Operations

## Create

### 1) Gather State

```bash
python scripts/gather_repo_state.py
```

Returns JSON:

```json
{
  "owner": "acme", "repo": "widget",
  "branch": "feat/add-auth", "base_branch": "develop",
  "on_base_branch": false, "has_staged": true,
  "staged_stat": "src/auth.py | 45 +++\n2 files changed",
  "commits_ahead": ["abc1234 feat(auth): add JWT validation"],
  "commits_ahead_count": 1
}
```

### 2) Determine Path

| Condition | Action |
| --------- | ------ |
| `on_base_branch=false` + `commits_ahead_count > 0` | Go to step 4 |
| `on_base_branch=true` + `has_staged=true` | Go to step 3 |
| `on_base_branch=true` + `has_staged=false` | Abort: "No staged changes to create PR from" |
| `on_base_branch=false` + `commits_ahead_count == 0` | Abort: "No commits ahead of base branch" |

### 3) Create Branch and Commit (from base branch)

1. Run `git diff --staged` to analyze changes
2. Generate conventional branch name (see [conventions.md](conventions.md))
3. Generate conventional commit message (see [conventions.md](conventions.md))
4. Execute:

```bash
git checkout -b <type>/<description>
git commit -m "<type>[scope]: <description>"
git push -u origin HEAD
```

### 4) Generate PR Content

**Title**: Conventional commit format, lowercase description after prefix.

- Convert branch to title: `feat/add-user-auth` -> `feat(auth): add user authentication`
- Infer scope from files changed or branch context

**Body**: Find the PR template using this fallback chain:

1. `.github/PULL_REQUEST_TEMPLATE.md` (relative to repo root)
2. First `.md` file in `.github/PULL_REQUEST_TEMPLATE/` directory
3. Skill-bundled `PULL_REQUEST_TEMPLATE.md` (alongside the skill file)

Read the template. Fill sections from diff, commits, and context. Leave placeholders for sections needing manual input. Remove inapplicable sections.

### 5) Create PR

Push the branch if no upstream tracking exists, then create the PR:

```bash
git push -u origin HEAD
gh pr create --title "<title>" --base "<base_branch>" --body "<body>"
```

For draft PRs, add `--draft` to the `gh pr create` command.

### 6) Report

Display the PR URL on success or error details on failure.

---

## Review

### Input

- Required: PR URL or `owner/repo#number`
- Optional: focus override after the identifier
  - `owner/repo#123 focus: security, tests`
  - `https://github.com/org/repo/pull/45 focus: error handling`

Focus override replaces the default checklist entirely.

### 1) Parse Input

Extract `owner`, `repo`, `number` from the PR reference (URL like `https://github.com/owner/repo/pull/N` or shorthand `owner/repo#N`). Parse optional focus override from the user's message text.

### 2) Fetch Context

```bash
python scripts/fetch_pr_context.py <owner> <repo> <number>
```

Returns JSON with metadata and filtered per-file diffs:

```json
{
  "title": "...", "author": "...", "base": "...", "head": "...",
  "additions": 120, "deletions": 15, "files": [...], "body": "...",
  "diff_files": [
    {"path": "src/auth.py", "diff": "@@...", "truncated": false},
    {"path": "src/service.py", "diff": "@@...", "truncated": true}
  ],
  "skipped_files": ["package-lock.json", "dist/bundle.js"],
  "diff_stats": {
    "total_files": 50, "shown_files": 30,
    "skipped_files": 18, "truncated_files": 2,
    "budget_exhausted": false
  }
}
```

The script auto-skips lockfiles, generated/minified files, vendored paths, and binary diffs. Files are prioritized by churn (additions + deletions). Defaults: 2000 total lines, 300 per file. Override with `--max-lines N` and `--max-file-lines N`. Use `--no-skip` to include all files.

If `diff_stats.budget_exhausted` is true, some files were omitted entirely — note partial scope in the review summary.

### 3) Determine Focus

Default (comprehensive):

- Correctness
- Readability
- Bugs / edge cases
- Security
- Performance
- Testing

If focus override provided, use only those areas.

### 4) Analyze Changes

Per file from `diff_files`:

- Review against selected focus areas
- Files are already filtered (noisy files excluded) and sorted by churn
- If any files were `truncated`, note that in your analysis
- If `budget_exhausted`, state which files were not reviewed

### 5) Build Review (do NOT submit)

- **Summary**: 1-3 bullets of key findings, focus areas used, partial scope note if applicable
- **Line comments**: `{path, line, side, body}` entries
  - Prefix body with `[critical]`, `[suggestion]`, or `[nit]`
- **Event**:
  - `REQUEST_CHANGES` if any `[critical]` issues
  - `COMMENT` otherwise
  - Never `APPROVE`

### 6) Present for Confirmation

Display to user before submitting:

- Summary body
- Every line comment (file, line, severity, body)
- Review event

Ask user to confirm. If declined, stop.

### 7) Submit via Script

After confirmation only. Write line comments to a temp JSON file:

```json
[
  {"path": "src/auth.py", "line": 42, "side": "RIGHT", "body": "[critical] SQL injection risk"},
  {"path": "src/utils.py", "line": 10, "side": "RIGHT", "body": "[nit] unused import"}
]
```

Submit:

```bash
python scripts/submit_review.py <owner> <repo> <number> <EVENT> "<summary>" /tmp/review-comments.json
```

The script handles both cases (with/without line comments) and enforces the never-APPROVE policy.

### 8) Report

- Total files reviewed
- Comments by severity
- Review event used

---

## Address Comments

### Input

- Required: PR URL or `owner/repo#number`

### 1) Parse Input and Fetch Context

Extract `owner`, `repo`, `number` from the PR reference.

```bash
python scripts/fetch_pr_context.py <owner> <repo> <number>
```

Returns metadata with filtered per-file diffs (same shape as Review step 2). Use `diff_files` for understanding change context per thread.

### 2) Fetch and Filter Review Threads

```bash
python scripts/fetch_threads.py <owner> <repo> <number>
```

Returns unresolved, non-outdated threads grouped by file path:

```json
[
  {
    "path": "src/auth.py",
    "threads": [
      {
        "thread_id": "...",
        "comments": [{"comment_id": 12345, "author": "reviewer", "body": "...", "line": 42}]
      }
    ]
  }
]
```

### 3) Checkout PR Branch

```bash
gh pr checkout <number> --repo <owner>/<repo>
```

### 4) Process Threads

For each unresolved, non-outdated thread:

1. **Read context**: open file at `path`, read surrounding lines
2. **Decide**: fix needed or no change warranted
3. **If fixing**: implement the minimal change
4. **Draft reply** (do not post yet):
   - Fixed: describe what changed and why (commit hash added after committing)
   - Not fixing: explain rationale clearly

After processing all threads, **group related fixes into logical commits**. Fixes that address the same concern or touch the same code area should be committed together. Validate each message before committing:

```bash
python scripts/validate_commit_msg.py "<message>"
git add <files>
git commit -m "<type>: <concise description>" \
  -m "Addresses review feedback on <path(s)>"
```

### 5) Push

```bash
git push
```

### 6) Reply to Threads

After successful push only. For each thread, post a reply using the `databaseId` of the first comment in the thread:

```bash
gh api --method POST "repos/<owner>/<repo>/pulls/<number>/comments/<comment_id>/replies" -f body="<reply>"
```

Examples:

- Fixed: `"Fixed in abc1234: switched to parameterized query"`
- Not fixing: `"Intentional: this import is used by the test harness via dynamic lookup"`

### 7) Report

- Total threads processed
- Threads fixed (with commit hashes)
- Threads declined (with rationale summaries)

### Constraints

- Never mark threads as resolved
- Never dismiss reviews
- Group related fixes into logical commits (by concern or code area, may span files)
- Implement only necessary fixes; no refactors or unrelated cleanup
- Reply to every unresolved thread, fixed or not
- Post replies only after successful push
