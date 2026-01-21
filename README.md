# skill-search

Search the [SkillsMP marketplace](https://skillsmp.com) for Claude Code skills relevant to your project.

## Features

- **Keyword Search**: Fast exact matching for technology names
- **AI Semantic Search**: Natural language queries powered by Cloudflare AI
- **Project Analysis**: Automatically detect your tech stack and find relevant skills
- **Install Skills**: Download and install skills directly from GitHub
- **Manage Skills**: List and uninstall installed skills
- **TUI Multi-Select**: Interactive terminal UI for selecting multiple skills to install
- **Auto-Update**: Silently updates itself to the latest version

## Installation

Clone this repository to your Claude Code skills directory:

```bash
git clone https://github.com/HateBunnyPlzzz/skill-search.git ~/.claude/skills/skill-search
```

## Setup

1. Get your free API key from https://skillsmp.com/docs/api

2. Run setup:
```bash
python3 ~/.claude/skills/skill-search/skill_search.py setup
```

3. Enter your API key when prompted

Alternatively, set the `SKILLSMP_API_KEY` environment variable.

## Usage

### In Claude Code

Simply ask Claude to find skills:
- "Find skills for React"
- "Search for testing skills"
- "Analyze this project and find relevant skills"
- "Find and install a skill for testing"

### Command Line

```bash
# Keyword search
python3 ~/.claude/skills/skill-search/skill_search.py search "react testing"

# Sort by popularity
python3 ~/.claude/skills/skill-search/skill_search.py search "docker" --sort stars

# AI semantic search (natural language)
python3 ~/.claude/skills/skill-search/skill_search.py ai "improve code quality"

# Interactive mode - search and install in one step
python3 ~/.claude/skills/skill-search/skill_search.py search "react" -i
python3 ~/.claude/skills/skill-search/skill_search.py ai "testing" --interactive

# TUI mode - multi-select skills with keyboard navigation
python3 ~/.claude/skills/skill-search/skill_search.py search "react" --tui
python3 ~/.claude/skills/skill-search/skill_search.py ai "testing" --tui

# Analyze project and find skills
python3 ~/.claude/skills/skill-search/skill_search.py analyze --dir /path/to/project
python3 ~/.claude/skills/skill-search/skill_search.py analyze --deep  # scan source files
```

## Commands

| Command | Description |
|---------|-------------|
| `setup` | Configure your API key |
| `search "query"` | Keyword search (exact matching) |
| `ai "query"` | AI semantic search (natural language) |
| `analyze` | Analyze project and find relevant skills |
| `install <url>` | Install skill from GitHub URL |
| `list` | List installed skills |
| `uninstall <name>` | Uninstall a skill |
| `update` | Check for and apply updates |

### Search Options

- `-n, --limit N` - Results per page (default: 10, max: 100)
- `-p, --page N` - Page number
- `--sort stars|recent` - Sort order
- `-i, --interactive` - Interactive mode: select and install skills from results
- `--tui` - TUI mode: multi-select skills with keyboard navigation

### Analyze Options

- `--dir PATH` - Project directory (default: current)
- `--deep` - Also scan source files

### Install Options

- `--name NAME` - Custom name for the skill folder
- `--force` - Overwrite existing skill

### Install Examples

```bash
# Install from a skill folder in a GitHub repo
python3 ~/.claude/skills/skill-search/skill_search.py install https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev/skills/skill-development

# Install with custom name
python3 ~/.claude/skills/skill-search/skill_search.py install https://github.com/owner/repo/tree/main/skills/my-skill --name custom-name

# Force reinstall
python3 ~/.claude/skills/skill-search/skill_search.py install <url> --force
```

### List & Uninstall

```bash
# List all installed skills
python3 ~/.claude/skills/skill-search/skill_search.py list

# Uninstall a skill
python3 ~/.claude/skills/skill-search/skill_search.py uninstall skill-name

# Uninstall without confirmation
python3 ~/.claude/skills/skill-search/skill_search.py uninstall skill-name -y
```

### Auto-Update

The skill **automatically updates itself** once per day when used. No action required - you're always on the latest version.

For manual control:
```bash
# Force update now
python3 ~/.claude/skills/skill-search/skill_search.py update

# Update all installed skills
python3 ~/.claude/skills/skill-search/skill_search.py update --all
```

### TUI Controls

When using `--tui` mode:
- `↑/↓` or `j/k` - Navigate up/down
- `Space` - Toggle selection
- `a` - Select all
- `n` - Clear selection
- `Enter` - Install selected skills
- `q` or `Esc` - Cancel

## How It Works

1. **Context Gathering**: Reads CLAUDE.md, package.json, requirements.txt, etc.
2. **Keyword Extraction**: Identifies technologies, frameworks, and concepts
3. **Smart Search**: Uses keyword search for tech names, AI search for goals
4. **Results**: Returns skill names, descriptions, authors, and URLs

## Requirements

- Python 3.7+
- No external dependencies (uses stdlib only)

## License

MIT License - see [LICENSE](LICENSE)

## Author

**hatebunnyplzzz** - [@hatebunnyplzzz](https://x.com/hatebunnyplzzz)

## Credits

- [SkillsMP](https://skillsmp.com) - Skills marketplace API
- Built for [Claude Code](https://claude.ai/claude-code)
