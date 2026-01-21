# skill-search

A Claude Code skill that searches the SkillsMP marketplace for community skills.

## Project Overview

This project provides a skill for Claude Code that allows users to discover and install skills from the SkillsMP marketplace (skillsmp.com). It's designed to be used both by Claude (via SKILL.md instructions) and directly by users in their terminal.

## Tech Stack

- **Language**: Python 3.7+ (stdlib only, no external dependencies)
- **API**: SkillsMP REST API (skillsmp.com)
- **TUI**: Python curses (for terminal-only multi-select)
- **VCS**: Git (for skill installation and auto-updates)

## Key Files

| File | Purpose |
|------|---------|
| `skill_search.py` | Main script - all commands and logic |
| `tui.py` | Terminal UI for multi-select (curses-based) |
| `SKILL.md` | Instructions for Claude Code on how to use this skill |
| `config.json` | Stores API key and settings (gitignored) |
| `README.md` | GitHub documentation |

## Architecture

```
skill_search.py
├── Config Management (load/save API key)
├── Auto-Update System (checks on skill load, pulls silently)
├── API Functions
│   ├── search_skills() - Keyword search
│   └── ai_search_skills() - Semantic search
├── Installation System
│   ├── install_skill_from_github() - Git sparse-checkout
│   ├── list_installed_skills()
│   └── uninstall_skill()
├── Output Formatting
│   ├── format_results() - Display search results
│   └── _run_tui_selection() - TUI mode (terminal only)
└── CLI Commands
    ├── setup, search, ai, analyze
    ├── install, list, uninstall
    └── update
```

## SkillsMP API

**Base URL**: `https://skillsmp.com/api/v1`

**Endpoints**:
- `GET /skills/search?q=...` - Keyword search
- `GET /skills/ai-search?q=...` - AI semantic search

**Auth**: `Authorization: Bearer <api_key>`

**Response**: JSON with `skills` array containing name, author, stars, description, skillUrl

## Important Constraints

### Claude Code Limitations
- **No TTY**: Claude runs commands without a terminal
- **No stdin**: `input()` causes EOFError
- **No curses**: TUI cannot render

**Solution**: Claude should use `install <url>` directly, never `-i` or `--tui` flags.

### Auto-Update Behavior
- Checks for updates on skill load (5-minute session window)
- Silently pulls updates via `git pull`
- No user notification - always on latest version

### Skill Installation
- Uses git sparse-checkout to download only skill folders
- Installs to `~/.claude/skills/<skill-name>/`
- Requires valid GitHub URL (converts SkillsMP URLs heuristically)

## Development Guidelines

1. **No external dependencies** - stdlib only for portability
2. **Graceful degradation** - Handle missing TTY, network errors, etc.
3. **Silent failures for auto-update** - Never interrupt user's command
4. **Clear error messages** - Help users fix issues themselves

## Testing

```bash
# Test search
python3 skill_search.py search "react"

# Test AI search
python3 skill_search.py ai "improve code quality"

# Test without TTY (simulates Claude Code)
echo "" | python3 skill_search.py search "react" -i

# Test TUI (terminal only)
python3 skill_search.py search "react" --tui
```

## Author

**hatebunnyplzzz** - [@hatebunnyplzzz](https://x.com/hatebunnyplzzz)

## Repository

https://github.com/HateBunnyPlzzz/skill-search
