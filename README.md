# skill-search

Search the [SkillsMP marketplace](https://skillsmp.com) for Claude Code skills relevant to your project.

## Features

- **Keyword Search**: Fast exact matching for technology names
- **AI Semantic Search**: Natural language queries powered by Cloudflare AI
- **Project Analysis**: Automatically detect your tech stack and find relevant skills

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

### Command Line

```bash
# Keyword search
python3 ~/.claude/skills/skill-search/skill_search.py search "react testing"

# Sort by popularity
python3 ~/.claude/skills/skill-search/skill_search.py search "docker" --sort stars

# AI semantic search (natural language)
python3 ~/.claude/skills/skill-search/skill_search.py ai "improve code quality"

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

### Search Options

- `-n, --limit N` - Results per page (default: 10, max: 100)
- `-p, --page N` - Page number
- `--sort stars\|recent` - Sort order

### Analyze Options

- `--dir PATH` - Project directory (default: current)
- `--deep` - Also scan source files

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
