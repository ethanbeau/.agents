# Git Naming Conventions

## Conventional Commit Specification

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Type Prefixes

| Prefix | Purpose | Version Bump |
|--------|---------|--------------|
| `feat:` | New feature | MINOR |
| `fix:` | Bug fix | PATCH |
| `docs:` | Documentation only | — |
| `style:` | Formatting, no code change | — |
| `refactor:` | Neither fix nor feature | — |
| `perf:` | Performance improvement | — |
| `test:` | Adding/updating tests | — |
| `build:` | Build system or dependencies | — |
| `ci:` | CI configuration | — |
| `chore:` | Other non-src/test changes | — |

### Scope

Parenthesized component identifier after type: `feat(api):`, `fix(auth):`, `docs(readme):`

Infer scope from affected files/directories when not obvious.

### Breaking Changes

Two ways to indicate (triggers MAJOR bump):

- `!` after type/scope: `feat!:`, `feat(api)!:`
- `BREAKING CHANGE:` footer in commit body

### 50/72 Formatting Rule

**Subject line**:

- Max 50 characters (including type/scope prefix)
- Lowercase first letter after prefix
- Imperative mood ("add feature" not "added feature")
- No trailing period
- Complete: "If applied, this commit will ..."

**Body** (optional):

- Blank line separating from subject
- Wrap at 72 characters per line
- Explain WHAT and WHY, not HOW
- Bullet points with `-` or `*`

**Footer** (optional):

- Blank line separating from body
- Issue references: `Closes #123`, `Refs #456`
- Breaking changes: `BREAKING CHANGE: description`

### Commit Generation

When generating commit messages:

1. Run `git diff --staged` (if nothing staged, ask user what to stage before proceeding)
2. If changes are ambiguous, ask for task description
3. Produce two options:

```bash
# Concise
git commit -m "<type>[scope]: <description>"

# Detailed
git commit -m "<type>[scope]: <description>" -m "<body>"
```

## Conventional Branch Specification

```text
<type>/<description>
```

### Branch Prefixes

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feat/` | New features | `feat/add-login-page` |
| `fix/` | Bug fixes | `fix/header-bug` |
| `hotfix/` | Urgent fixes | `hotfix/security-patch` |
| `release/` | Release prep | `release/v1.2.0` |
| `chore/` | Non-code tasks | `chore/update-dependencies` |
| `docs/` | Documentation | `docs/update-api-reference` |
| `refactor/` | Refactoring | `refactor/extract-auth-module` |
| `test/` | Tests | `test/add-integration-tests` |
| `ci/` | CI configuration | `ci/add-deploy-pipeline` |
| `build/` | Build system | `build/upgrade-webpack` |
| `perf/` | Performance | `perf/optimize-query` |
| `style/` | Formatting | `style/fix-lint-errors` |

### Rules

1. Lowercase alphanumerics, hyphens, and dots only
2. No consecutive, leading, or trailing hyphens or dots
3. Dots permitted only in release version descriptions (e.g., `release/v1.2.0`)
4. Clear and concise — indicates the purpose of the work

### Branch Generation

1. Analyze staged/unstaged changes or ask for context
2. Generate: `git checkout -b <type>/<description>`

## PR Title Convention

PR titles follow the commit format: `<type>[scope]: <description>`

- Description after prefix MUST be lowercase (no initial capital)
- Infer scope from files changed or branch context
- Convert branch to title: `feat/add-user-auth` -> `feat(auth): add user authentication`
