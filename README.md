# 🤖 .agents

A curated collection of ethanbeau's AI agent configurations, custom skills, and workspace rules.

## Quick Setup

```bash
cd ~/.agents
bash scripts/setup.sh
```

What `scripts/setup.sh` does:

- Installs Homebrew (if missing)
- Installs dependencies from `Brewfile` (`gh`, `python`, `stow`, etc.)
- Prepares the environment for custom skills and automation

## Update everything

```bash
cd ~/.agents
bash scripts/update.sh
```

What `scripts/update.sh` does:

- `git pull`
- `brew update`
- `brew upgrade`
- `brew cleanup`

## Structure

- `skills/` — Custom agent skills (e.g., `git-workflow`)
- `settings/` — Global configuration for AI agents
- `rules/` — AI instruction sets and repository-level guidelines
- `scripts/` — Bootstrap and maintenance scripts
- `Brewfile` — Required CLI tools and dependencies
- `memory/` — Persistent memory and context for agents

## Custom Skills

### Git Workflow

Handles complex git operations including worktree creation, conventional commits, and PR management.
Requires: `gh` CLI, `python3`.
