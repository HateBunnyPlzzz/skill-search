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

# JSON output (RECOMMENDED for Claude - easier to parse)
python3 ~/.claude/skills/skill-search/skill_search.py search "keywords" --json
python3 ~/.claude/skills/skill-search/skill_search.py ai "query" --json
```

**JSON output format:**
```json
{
  "skills": [
    {
      "name": "skill-name",
      "author": "author-name",
      "stars": 123,
      "description": "What the skill does...",
      "url": "https://skillsmp.com/skills/...",
      "github_url": "https://github.com/owner/repo/tree/main/path"
    }
  ]
}
```

### Step 4: Present Results

Show the user:
- Skill name
- Author
- Stars (popularity)
- Description (what it does)
- URL (to view full skill)

### Step 5: Install (Interactive Selection)

**IMPORTANT**: Use Claude Code's native `AskUserQuestion` tool for skill selection!

**Workflow:**
1. Run search command (no `-i` or `--tui` flags)
2. Parse the JSON-like output or display results to user
3. Use `AskUserQuestion` tool with multi-select to let user choose skills
4. Run `install` command for each selected skill

**Example AskUserQuestion usage:**
```
After getting search results, use AskUserQuestion with:
- header: "Skills"
- question: "Which skills would you like to install?"
- multiSelect: true
- options: [
    { label: "skill-name-1 (123 stars)", description: "Brief description of what it does" },
    { label: "skill-name-2 (45 stars)", description: "Brief description of what it does" },
    { label: "skill-name-3 (12 stars)", description: "Brief description of what it does" },
    { label: "None - just browsing", description: "Don't install any skills" }
  ]
```

**Then install selected skills:**
```bash
# For each selected skill, run:
python3 ~/.claude/skills/skill-search/skill_search.py install <github-url>
```

**WHY NOT use `-i` or `--tui` flags?**
These require a real terminal (TTY) and will fail when run by Claude Code.
The `AskUserQuestion` tool provides the same interactive experience using
Claude Code's native UI (arrow keys, multi-select, etc.).

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

### Install Skill
```bash
python3 ~/.claude/skills/skill-search/skill_search.py install <github-url> [--name NAME] [--force]
```

Options:
- `--name NAME` - Custom name for skill folder
- `--force` - Overwrite existing skill

### List Installed Skills
```bash
python3 ~/.claude/skills/skill-search/skill_search.py list
```

### Uninstall Skill
```bash
python3 ~/.claude/skills/skill-search/skill_search.py uninstall <skill-name> [-y]
```

### Update Skills
```bash
# Force update now
python3 ~/.claude/skills/skill-search/skill_search.py update

# Update all installed skills
python3 ~/.claude/skills/skill-search/skill_search.py update --all
```

**Auto-update**: The skill automatically updates itself once per day when used. No notification - you're always on the latest version.

### TUI Mode (Multi-Select)
```bash
# Use TUI for multi-select installation
python3 ~/.claude/skills/skill-search/skill_search.py search "react" --tui
python3 ~/.claude/skills/skill-search/skill_search.py ai "testing" --tui
```

**TUI Controls:**
- `↑/↓` or `j/k` - Navigate
- `Space` - Toggle selection
- `a` - Select all | `n` - Clear all
- `Enter` - Install selected
- `q/Esc` - Cancel

## Example Workflows

### Example 1: "Find relevant skills for this project"

**Step 1: Read CLAUDE.md** (if exists in project root)
```
# Read the project's CLAUDE.md to understand context
Read tool: /path/to/project/CLAUDE.md
```

**Step 2: Analyze the CLAUDE.md content**
Example CLAUDE.md content:
```markdown
# MyApp - E-commerce Platform

## Tech Stack
- Next.js 14 with App Router
- TypeScript
- Prisma ORM with PostgreSQL
- TailwindCSS + shadcn/ui
- Jest + React Testing Library

## Current Goals
- Improve test coverage to 80%
- Add end-to-end tests with Playwright
- Optimize database queries for product listings
```

**Step 3: Extract keywords from context**
- Technologies: `nextjs`, `typescript`, `prisma`, `postgresql`, `tailwind`, `shadcn`, `jest`
- Goals: `testing`, `e2e`, `playwright`, `database optimization`

**Step 4: Run targeted searches**
```bash
# Search for tech-stack specific skills
python3 ~/.claude/skills/skill-search/skill_search.py search "nextjs prisma typescript" --sort stars -n 5

# Search for goal-based skills using AI
python3 ~/.claude/skills/skill-search/skill_search.py ai "improve test coverage e2e testing playwright react"

# Search for performance optimization
python3 ~/.claude/skills/skill-search/skill_search.py ai "database query optimization prisma postgresql"
```

**Step 5: Present results with relevance explanation**
```
Based on your CLAUDE.md, I found these relevant skills:

FOR YOUR TECH STACK (Next.js + Prisma + TypeScript):
1. vercel-react-best-practices (126k stars) - React/Next.js performance patterns
2. prisma-best-practices (15k stars) - Prisma ORM optimization
   → Relevant: You mentioned optimizing database queries

FOR YOUR TESTING GOALS:
3. playwright-testing (8k stars) - E2E testing with Playwright
   → Relevant: Matches your goal of adding Playwright tests
4. jest-react-testing (12k stars) - Jest + RTL patterns
   → Relevant: Matches your current Jest setup

Would you like me to install any of these?
```

---

### Example 2: "What skills would help with this Next.js app?"

**Claude's workflow:**

1. **Check for package.json** to get exact dependencies:
```json
{
  "dependencies": {
    "next": "14.0.0",
    "react": "18.2.0",
    "@prisma/client": "5.0.0",
    "zod": "3.22.0",
    "@tanstack/react-query": "5.0.0"
  },
  "devDependencies": {
    "typescript": "5.0.0",
    "vitest": "1.0.0",
    "playwright": "1.40.0"
  }
}
```

2. **Extract specific dependencies**:
   - Framework: Next.js 14, React 18
   - Database: Prisma
   - Validation: Zod
   - State: React Query
   - Testing: Vitest, Playwright

3. **Run multiple targeted searches**:
```bash
# Core framework
python3 ~/.claude/skills/skill-search/skill_search.py search "nextjs 14 app router" --sort stars -n 5

# Specific libraries
python3 ~/.claude/skills/skill-search/skill_search.py search "zod validation typescript" --sort stars -n 3
python3 ~/.claude/skills/skill-search/skill_search.py search "react-query tanstack" --sort stars -n 3

# Testing stack
python3 ~/.claude/skills/skill-search/skill_search.py search "vitest playwright" --sort stars -n 5
```

---

### Example 3: "Analyze this project and suggest skills"

**Use the built-in analyze command:**
```bash
python3 ~/.claude/skills/skill-search/skill_search.py analyze --dir /path/to/project --deep
```

**Output:**
```
======================================================================
PROJECT ANALYSIS
======================================================================

Detected Technologies: docker, javascript, nextjs, nodejs, npm, prisma,
                       react, tailwind, typescript
Extracted Keywords: api, authentication, database, frontend, jwt,
                    testing, validation

Detected Goals:
  - improve performance of the dashboard page
  - add comprehensive error handling

CLAUDE.md Preview:
  # E-commerce Admin Dashboard...

======================================================================
SEARCHING FOR RELEVANT SKILLS
======================================================================

Searching by technology: 'nextjs typescript prisma'
[Results displayed...]

AI searching by context: 'improve performance of the dashboard page...'
[Results displayed...]
```

---

### Example 4: "Find and install a code review skill"

**Claude's workflow using AskUserQuestion:**

**Step 1: Search (no -i flag)**
```bash
python3 ~/.claude/skills/skill-search/skill_search.py search "code review" --sort stars -n 4
```

**Step 2: Parse results and show to user**
```
I found these code review skills:

1. code-review (96 stars) - Automated PR code review with multi-agent analysis
2. ai-code-reviewer (12 stars) - AI-powered code review on git hooks
3. pr-reviewer (8 stars) - GitHub PR review automation
4. review-assistant (5 stars) - Code review checklist generator
```

**Step 3: Use AskUserQuestion for selection**
```
Claude uses AskUserQuestion tool:
{
  "questions": [{
    "header": "Install",
    "question": "Which code review skill(s) would you like to install?",
    "multiSelect": true,
    "options": [
      { "label": "code-review (96 stars)", "description": "Automated PR code review with multi-agent analysis" },
      { "label": "ai-code-reviewer (12 stars)", "description": "AI-powered code review on git hooks" },
      { "label": "pr-reviewer (8 stars)", "description": "GitHub PR review automation" },
      { "label": "None", "description": "Don't install any skills right now" }
    ]
  }]
}
```

**User sees Claude Code's native multi-select UI with arrow keys!**

**Step 4: Install selected skills**
```bash
# User selected "code-review", so Claude runs:
python3 ~/.claude/skills/skill-search/skill_search.py install https://github.com/aiskillstore/marketplace-skills/tree/main/bind/code-review
```

**Result:**
```
Success! Skill installed to: /Users/you/.claude/skills/code-review
```

---

### Example 5: Python ML Project

**CLAUDE.md content:**
```markdown
# ML Pipeline

## Stack
- Python 3.11
- PyTorch 2.0
- FastAPI for serving
- MLflow for experiment tracking

## Needs
- Better model versioning workflow
- Automated hyperparameter tuning
- API documentation generation
```

**Claude's search strategy:**
```bash
# ML-specific skills
python3 ~/.claude/skills/skill-search/skill_search.py search "pytorch mlflow" --sort stars -n 5

# Goal-based AI search
python3 ~/.claude/skills/skill-search/skill_search.py ai "machine learning model versioning hyperparameter tuning mlops"

# API documentation
python3 ~/.claude/skills/skill-search/skill_search.py search "fastapi openapi documentation" --sort stars -n 5
```

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
