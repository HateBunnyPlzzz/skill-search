---
name: skill-search
description: |
  Search SkillsMP marketplace for Claude Code skills relevant to the current project.
  Use when: (1) user asks "find skills for...", "search for skills", "is there a skill for..."
  (2) user wants to improve workflows, find better tools, or discover community solutions
  (3) starting a new project and want to find relevant skills
  (4) user explicitly mentions SkillsMP or skill marketplace

  This skill reads CLAUDE.md to understand project context, extracts intelligent keywords,
  and searches the SkillsMP database for relevant community skills.
author: hatebunnyplzzz
version: 1.0.0
---

# Skill Search

Search the SkillsMP marketplace (skillsmp.com) for Claude Code skills relevant to your project.

## Prerequisites

**API Key Required**: Get your free API key from https://skillsmp.com/docs/api

First-time setup:
```bash
python3 ~/.claude/skills/skill-search/skill_search.py setup
```

## How This Skill Works

### Step 1: Understand Context

Before searching, Claude should gather context:

1. **Read CLAUDE.md** (if exists) to understand:
   - Project type and goals
   - Technologies being used
   - Current pain points or areas needing improvement
   - Existing workflows

2. **Optionally analyze codebase** (only if user requests):
   - Check package.json, requirements.txt, Cargo.toml, etc.
   - Identify frameworks and libraries
   - Understand project structure

### Step 2: Extract Keywords

From the context, extract:
- **Technology keywords**: react, python, typescript, docker, etc.
- **Task keywords**: testing, deployment, documentation, api, etc.
- **Goal keywords**: performance, security, automation, ui, etc.

### Step 3: Search

Use the extracted keywords to search:

```bash
# Keyword search (exact matching, fast)
python3 ~/.claude/skills/skill-search/skill_search.py search "keywords here"

# AI semantic search (natural language, better for goals)
python3 ~/.claude/skills/skill-search/skill_search.py ai "describe what you need"
```

### Step 4: Present Results

Show the user:
- Skill name
- Author
- Stars (popularity)
- Description (what it does)
- URL (to view full skill)

## Commands

### Setup (First Time)
```bash
python3 ~/.claude/skills/skill-search/skill_search.py setup
```
Prompts for API key and saves it.

### Keyword Search
```bash
python3 ~/.claude/skills/skill-search/skill_search.py search "react testing" [options]
```

Options:
- `-n, --limit N` - Results per page (default: 10, max: 100)
- `-p, --page N` - Page number for pagination
- `--sort stars|recent` - Sort by popularity or recency

### AI Semantic Search
```bash
python3 ~/.claude/skills/skill-search/skill_search.py ai "how to improve frontend performance"
```

Uses Cloudflare AI for natural language understanding.

### Analyze Project
```bash
python3 ~/.claude/skills/skill-search/skill_search.py analyze [--dir PATH] [--deep]
```

Options:
- `--dir PATH` - Project directory (default: current)
- `--deep` - Also scan source files (slower but more thorough)

## Example Workflows

### User: "Find skills for my React project"

Claude should:
1. Read CLAUDE.md to understand the project
2. Check for package.json to identify dependencies
3. Extract keywords: "react", framework names, any pain points mentioned
4. Run search:
```bash
python3 ~/.claude/skills/skill-search/skill_search.py search "react" --sort stars -n 10
```

### User: "I want better testing skills"

Claude should:
1. Identify what tech stack is being used
2. Run AI search:
```bash
python3 ~/.claude/skills/skill-search/skill_search.py ai "testing skills for [detected stack]"
```

### User: "Analyze this project and find relevant skills"

Claude should:
1. Run analyze command:
```bash
python3 ~/.claude/skills/skill-search/skill_search.py analyze --dir . --deep
```
2. Review extracted keywords
3. Search for skills based on analysis

## Best Practices for Claude

1. **Always read context first** - Don't just search blindly
2. **Be specific with keywords** - "react testing" > "testing"
3. **Use AI search for goals** - "improve performance" works better with AI search
4. **Use keyword search for tech** - "nextjs", "prisma" work better with keyword search
5. **Show top 5-10 results** - Don't overwhelm the user
6. **Explain relevance** - Tell user why each skill might help

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/skills/search` | GET | Keyword search |
| `/api/v1/skills/ai-search` | GET | AI semantic search |

Authentication: `Authorization: Bearer <api_key>`
