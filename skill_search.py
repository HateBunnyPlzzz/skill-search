#!/usr/bin/env python3
"""
Skill Search - Find relevant Claude Code skills from SkillsMP marketplace.

Usage:
    python3 skill_search.py setup                    # Configure API key
    python3 skill_search.py search "query"           # Keyword search
    python3 skill_search.py ai "natural language"    # AI semantic search
    python3 skill_search.py analyze [--dir PATH]     # Analyze project
    python3 skill_search.py install <github-url>     # Install a skill
    python3 skill_search.py update                   # Check for updates

API: https://skillsmp.com/docs/api
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlparse

# Auto-update check interval (5 minutes = new session/skill load)
UPDATE_CHECK_INTERVAL = 300

# Configuration
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
BASE_URL = "https://skillsmp.com"
SKILLS_DIR = Path.home() / ".claude" / "skills"

# Technology detection patterns
TECH_PATTERNS = {
    # Package managers / Languages
    "package.json": ["javascript", "nodejs", "npm"],
    "package-lock.json": ["nodejs", "npm"],
    "yarn.lock": ["nodejs", "yarn"],
    "pnpm-lock.yaml": ["nodejs", "pnpm"],
    "requirements.txt": ["python"],
    "pyproject.toml": ["python"],
    "Pipfile": ["python", "pipenv"],
    "Cargo.toml": ["rust"],
    "go.mod": ["golang", "go"],
    "Gemfile": ["ruby"],
    "composer.json": ["php"],
    "pom.xml": ["java", "maven"],
    "build.gradle": ["java", "gradle"],
    "build.gradle.kts": ["kotlin", "gradle"],

    # Frameworks
    "next.config.js": ["nextjs", "react"],
    "next.config.mjs": ["nextjs", "react"],
    "next.config.ts": ["nextjs", "react", "typescript"],
    "nuxt.config.js": ["nuxt", "vue"],
    "nuxt.config.ts": ["nuxt", "vue", "typescript"],
    "vite.config.js": ["vite"],
    "vite.config.ts": ["vite", "typescript"],
    "svelte.config.js": ["svelte"],
    "astro.config.mjs": ["astro"],
    "remix.config.js": ["remix", "react"],
    "angular.json": ["angular", "typescript"],
    "vue.config.js": ["vue"],

    # TypeScript
    "tsconfig.json": ["typescript"],

    # Styling
    "tailwind.config.js": ["tailwind", "css"],
    "tailwind.config.ts": ["tailwind", "css", "typescript"],
    "postcss.config.js": ["postcss", "css"],
    "styled-components": ["styled-components", "css-in-js"],

    # Testing
    "jest.config.js": ["jest", "testing"],
    "jest.config.ts": ["jest", "testing", "typescript"],
    "vitest.config.ts": ["vitest", "testing"],
    "pytest.ini": ["pytest", "testing", "python"],
    "cypress.config.js": ["cypress", "e2e-testing"],
    "playwright.config.ts": ["playwright", "e2e-testing"],

    # DevOps
    "Dockerfile": ["docker", "containers"],
    "docker-compose.yml": ["docker", "docker-compose"],
    "docker-compose.yaml": ["docker", "docker-compose"],
    ".github/workflows": ["github-actions", "ci-cd"],
    ".gitlab-ci.yml": ["gitlab-ci", "ci-cd"],
    "Jenkinsfile": ["jenkins", "ci-cd"],
    "terraform": ["terraform", "infrastructure"],
    "kubernetes": ["kubernetes", "k8s"],

    # Database
    "prisma": ["prisma", "database", "orm"],
    "drizzle.config.ts": ["drizzle", "database", "orm"],
    ".env": ["environment", "config"],

    # API
    "openapi.yaml": ["openapi", "api"],
    "swagger.json": ["swagger", "api"],
    "graphql": ["graphql", "api"],

    # Documentation
    "README.md": ["documentation"],
    "docs/": ["documentation"],
    "CLAUDE.md": ["claude-code"],
}

# Keywords to extract from text content
KEYWORD_EXTRACTORS = [
    # Frameworks and libraries
    r"\b(react|vue|angular|svelte|nextjs|nuxt|remix|astro)\b",
    r"\b(express|fastify|nestjs|django|flask|fastapi|rails)\b",
    r"\b(prisma|drizzle|typeorm|sequelize|mongoose)\b",
    r"\b(tailwind|bootstrap|material-ui|chakra|shadcn)\b",
    r"\b(jest|vitest|pytest|mocha|cypress|playwright)\b",
    r"\b(docker|kubernetes|terraform|aws|gcp|azure)\b",
    r"\b(graphql|rest|grpc|websocket|trpc)\b",
    r"\b(postgresql|mysql|mongodb|redis|sqlite)\b",

    # Languages
    r"\b(typescript|javascript|python|rust|golang|java|ruby|php)\b",

    # Concepts
    r"\b(authentication|authorization|auth|oauth|jwt)\b",
    r"\b(testing|test|e2e|unit-test|integration)\b",
    r"\b(deployment|deploy|ci-cd|pipeline)\b",
    r"\b(performance|optimization|caching)\b",
    r"\b(security|encryption|vulnerability)\b",
    r"\b(documentation|docs|readme)\b",
    r"\b(api|backend|frontend|fullstack)\b",
    r"\b(database|orm|migration|schema)\b",
    r"\b(ui|ux|design|component|styling)\b",
    r"\b(git|version-control|branching)\b",
    r"\b(debugging|logging|monitoring|observability)\b",
    r"\b(automation|scripting|workflow)\b",
]


def load_config():
    """Load API configuration."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config):
    """Save API configuration."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def should_check_for_updates():
    """
    Check if this is a new skill load (session).
    Uses a 5-minute window to detect new sessions vs continued use.
    """
    config = load_config()
    last_check = config.get("last_update_check", 0)
    return (time.time() - last_check) > UPDATE_CHECK_INTERVAL


def record_update_check():
    """Record that we just checked for updates."""
    config = load_config()
    config["last_update_check"] = time.time()
    save_config(config)


def auto_check_for_updates():
    """
    Silently check for and apply updates when skill is loaded.
    Runs once per session (5-minute window). Updates are applied automatically.
    """
    if not should_check_for_updates():
        return

    # Check if this is a git repo
    git_dir = SCRIPT_DIR / ".git"
    if not git_dir.exists():
        return

    try:
        # Fetch silently
        subprocess.run(
            ["git", "-C", str(SCRIPT_DIR), "fetch", "--quiet"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Check if behind
        result = subprocess.run(
            ["git", "-C", str(SCRIPT_DIR), "rev-list", "--count", "HEAD..@{upstream}"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            behind = int(result.stdout.strip())
            if behind > 0:
                # Auto-apply updates silently
                subprocess.run(
                    ["git", "-C", str(SCRIPT_DIR), "pull", "--quiet"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

    except Exception:
        pass  # Silently fail - don't interrupt user's command

    # Record that we checked (even if it failed)
    record_update_check()


def get_api_key():
    """Get API key from config or environment."""
    config = load_config()
    api_key = config.get("api_key") or os.environ.get("SKILLSMP_API_KEY")

    if not api_key:
        print("Error: No API key configured.", file=sys.stderr)
        print("Run: python3 skill_search.py setup", file=sys.stderr)
        print("Or set SKILLSMP_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    return api_key


def api_request(endpoint, api_key):
    """Make authenticated API request."""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "SkillSearch/1.0"
    }

    req = Request(url, headers=headers)

    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            err = json.loads(body)
            code = err.get("error", {}).get("code", "UNKNOWN")
            msg = err.get("error", {}).get("message", body)
            print(f"API Error ({code}): {msg}", file=sys.stderr)
        except:
            print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        return None
    except URLError as e:
        print(f"Connection Error: {e.reason}", file=sys.stderr)
        return None


def extract_keywords_from_text(text):
    """Extract technology and concept keywords from text."""
    text_lower = text.lower()
    keywords = set()

    for pattern in KEYWORD_EXTRACTORS:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        keywords.update(matches)

    return list(keywords)


def analyze_project(directory=".", deep=False):
    """
    Analyze a project directory to extract relevant keywords.

    Returns:
        dict with keys: technologies, concepts, goals, raw_keywords
    """
    project_dir = Path(directory).resolve()
    result = {
        "technologies": set(),
        "concepts": set(),
        "goals": [],
        "raw_keywords": set(),
        "context": "",
    }

    # 1. Check for CLAUDE.md first - most valuable context
    for claude_file in ["CLAUDE.md", ".claude/CLAUDE.md", "claude.md"]:
        claude_path = project_dir / claude_file
        if claude_path.exists():
            try:
                content = claude_path.read_text(encoding="utf-8")
                result["context"] = content[:3000]

                # Extract keywords from CLAUDE.md
                keywords = extract_keywords_from_text(content)
                result["raw_keywords"].update(keywords)

                # Look for goals/objectives
                goal_patterns = [
                    r"(?:goal|objective|purpose|aim)s?[:\s]+([^\n]+)",
                    r"(?:should|must|need to|want to)[:\s]+([^\n]+)",
                    r"(?:improve|enhance|optimize|better)[:\s]+([^\n]+)",
                ]
                for pattern in goal_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    result["goals"].extend(matches[:5])

            except Exception as e:
                print(f"Warning: Could not read {claude_file}: {e}", file=sys.stderr)

    # 2. Detect technologies from files
    for file_pattern, techs in TECH_PATTERNS.items():
        check_path = project_dir / file_pattern
        if check_path.exists() or list(project_dir.glob(file_pattern)):
            result["technologies"].update(techs)

    # 3. Check package.json for dependencies (very valuable)
    package_json = project_dir / "package.json"
    if package_json.exists():
        try:
            with open(package_json) as f:
                pkg = json.load(f)

            # Extract from dependencies
            all_deps = {}
            all_deps.update(pkg.get("dependencies", {}))
            all_deps.update(pkg.get("devDependencies", {}))

            # Map common packages to keywords
            dep_keywords = {
                "react": ["react", "frontend"],
                "next": ["nextjs", "react", "fullstack"],
                "vue": ["vue", "frontend"],
                "nuxt": ["nuxt", "vue", "fullstack"],
                "express": ["express", "nodejs", "backend", "api"],
                "fastify": ["fastify", "nodejs", "backend", "api"],
                "@nestjs": ["nestjs", "nodejs", "backend", "api"],
                "prisma": ["prisma", "database", "orm"],
                "drizzle": ["drizzle", "database", "orm"],
                "tailwind": ["tailwind", "css", "styling"],
                "jest": ["jest", "testing"],
                "vitest": ["vitest", "testing"],
                "cypress": ["cypress", "e2e", "testing"],
                "playwright": ["playwright", "e2e", "testing"],
                "typescript": ["typescript"],
                "graphql": ["graphql", "api"],
                "@trpc": ["trpc", "api", "typescript"],
                "zod": ["zod", "validation", "typescript"],
            }

            for dep in all_deps:
                for key, keywords in dep_keywords.items():
                    if key in dep.lower():
                        result["technologies"].update(keywords)

        except Exception as e:
            print(f"Warning: Could not parse package.json: {e}", file=sys.stderr)

    # 4. Check requirements.txt for Python deps
    requirements = project_dir / "requirements.txt"
    if requirements.exists():
        try:
            content = requirements.read_text()
            python_keywords = {
                "django": ["django", "python", "backend", "web"],
                "flask": ["flask", "python", "backend", "api"],
                "fastapi": ["fastapi", "python", "backend", "api"],
                "pytest": ["pytest", "testing", "python"],
                "pandas": ["pandas", "data-science", "python"],
                "numpy": ["numpy", "data-science", "python"],
                "tensorflow": ["tensorflow", "machine-learning", "ai"],
                "pytorch": ["pytorch", "machine-learning", "ai"],
                "langchain": ["langchain", "llm", "ai"],
                "openai": ["openai", "llm", "ai"],
            }

            for pkg, keywords in python_keywords.items():
                if pkg in content.lower():
                    result["technologies"].update(keywords)

        except Exception as e:
            print(f"Warning: Could not read requirements.txt: {e}", file=sys.stderr)

    # 5. Deep scan (optional) - check source files
    if deep:
        source_patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.tsx", "**/*.jsx"]
        for pattern in source_patterns:
            for file in list(project_dir.glob(pattern))[:50]:  # Limit to 50 files
                if "node_modules" in str(file) or ".git" in str(file):
                    continue
                try:
                    content = file.read_text(encoding="utf-8")[:5000]
                    keywords = extract_keywords_from_text(content)
                    result["raw_keywords"].update(keywords)
                except:
                    pass

    # Convert sets to lists for JSON serialization
    result["technologies"] = sorted(result["technologies"])
    result["concepts"] = sorted(result["concepts"])
    result["raw_keywords"] = sorted(result["raw_keywords"])

    return result


def search_skills(query, api_key, limit=10, page=1, sort_by=None):
    """Keyword search for skills."""
    endpoint = f"/api/v1/skills/search?q={quote_plus(query)}&limit={limit}&page={page}"
    if sort_by:
        endpoint += f"&sortBy={sort_by}"
    return api_request(endpoint, api_key)


def ai_search_skills(query, api_key):
    """AI semantic search for skills."""
    endpoint = f"/api/v1/skills/ai-search?q={quote_plus(query)}"
    return api_request(endpoint, api_key)


def skillsmp_url_to_github(skillsmp_url):
    """
    Try to convert a SkillsMP URL to a GitHub URL.

    SkillsMP URL format: skillsmp.com/skills/owner-repo-path-skill-md
    This is a best-effort conversion as the format is ambiguous.
    """
    if not skillsmp_url or "skillsmp.com/skills/" not in skillsmp_url:
        return None

    # Extract the slug part
    slug = skillsmp_url.split("skillsmp.com/skills/")[-1]

    # Remove -skill-md suffix
    if slug.endswith("-skill-md"):
        slug = slug[:-9]

    # Split by dashes
    parts = slug.split("-")

    if len(parts) < 2:
        return None

    # First part is owner
    owner = parts[0]

    # Try to find repo name - usually the second part or first two parts
    # This is heuristic-based and won't always work
    repo = parts[1]
    path_start = 2

    # Common patterns: owner-repo-name-path or owner-repo-path
    # Try combining parts until we find a reasonable split
    if len(parts) > 2 and parts[1] in ["claude", "claude-code", "skills", "awesome"]:
        # Likely a multi-word repo name
        for i in range(2, min(5, len(parts))):
            test_repo = "-".join(parts[1:i+1])
            if any(x in test_repo for x in ["claude", "skills", "code", "prompts", "config"]):
                repo = test_repo
                path_start = i + 1
                break

    # Remaining parts form the path
    if path_start < len(parts):
        path = "/".join(parts[path_start:])
    else:
        path = ""

    # Construct GitHub URL
    if path:
        return f"https://github.com/{owner}/{repo}/tree/main/{path}"
    else:
        return f"https://github.com/{owner}/{repo}"


def format_results(response, is_ai_search=False, interactive=False, use_tui=False, json_output=False):
    """Format and print search results."""
    if not response or not response.get("success"):
        print("No results found or API error.")
        return []

    data = response.get("data", {})

    # Handle different response formats
    if is_ai_search:
        items = data.get("data", [])
        skills = [item.get("skill") for item in items if item.get("skill")]
    else:
        skills = data.get("skills", [])
        pagination = data.get("pagination", {})

    if not skills:
        print("No skills found matching your query.")
        return []

    # Use TUI if requested
    if use_tui and skills:
        return _run_tui_selection(skills)

    # JSON output mode (for Claude to parse easily)
    if json_output and skills:
        output = {
            "skills": [
                {
                    "name": s.get("name", "Unknown"),
                    "author": s.get("author", "Unknown"),
                    "stars": s.get("stars", 0),
                    "description": s.get("description", "")[:200],
                    "url": s.get("skillUrl", ""),
                    "github_url": s.get("githubUrl") or skillsmp_url_to_github(s.get("skillUrl", ""))
                }
                for s in skills
            ]
        }
        print(json.dumps(output, indent=2))
        return skills

    # Print header
    if not is_ai_search and "pagination" in data:
        p = data["pagination"]
        print(f"\n{'='*70}")
        print(f"Found {p.get('total', len(skills))} skills (Page {p.get('page', 1)}/{p.get('totalPages', 1)})")
        print(f"{'='*70}\n")
    else:
        print(f"\n{'='*70}")
        print(f"Found {len(skills)} relevant skills")
        print(f"{'='*70}\n")

    # Print each skill
    for i, skill in enumerate(skills, 1):
        name = skill.get("name", "Unknown")
        author = skill.get("author", "Unknown")
        stars = skill.get("stars", 0)
        desc = skill.get("description", "No description")
        url = skill.get("skillUrl", "")

        print(f"{i}. {name}")
        print(f"   Author: {author} | Stars: {stars}")
        print(f"   {desc[:200]}{'...' if len(desc) > 200 else ''}")
        if url:
            print(f"   URL: {url}")
        print()

    # Interactive installation prompt
    if interactive and skills:
        # Check if stdin is available (TTY) - fails when run by Claude Code
        if not sys.stdin.isatty():
            print("-" * 70)
            print("NOTE: Interactive mode requires a terminal.")
            print("To install a skill, use:")
            print("  python3 skill_search.py install <github-url>")
            print("-" * 70)
            return skills

        print("-" * 70)
        print("Enter skill number to install (or 'q' to quit):")

        while True:
            try:
                choice = input("> ").strip().lower()

                if choice in ('q', 'quit', 'exit', ''):
                    break

                idx = int(choice) - 1
                if 0 <= idx < len(skills):
                    skill = skills[idx]
                    skillsmp_url = skill.get("skillUrl", "")
                    github_url = skill.get("githubUrl") or skillsmp_url_to_github(skillsmp_url)

                    if github_url:
                        print(f"\nAttempting to install from: {github_url}")
                        success = install_skill_from_github(github_url)
                        if success:
                            print("\nEnter another number or 'q' to quit:")
                        else:
                            print("\nInstallation failed. The GitHub URL may be incorrect.")
                            print(f"Try visiting: {skillsmp_url}")
                            print("and find the actual GitHub source URL.\n")
                    else:
                        print(f"\nCouldn't determine GitHub URL for this skill.")
                        print(f"Visit: {skillsmp_url}")
                        print("to find the GitHub source URL, then use:")
                        print(f"  skill_search.py install <github-url>\n")
                else:
                    print(f"Invalid choice. Enter 1-{len(skills)} or 'q'")
            except ValueError:
                print(f"Invalid input. Enter a number 1-{len(skills)} or 'q'")
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled.")
                break

    return skills


def _run_tui_selection(skills):
    """Run the TUI for skill selection and install selected skills."""
    # TUI requires a real terminal
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("-" * 70)
        print("NOTE: TUI mode requires a terminal.")
        print("To install skills, use the install command directly:")
        print("  python3 skill_search.py install <github-url>")
        print("-" * 70)
        return skills

    try:
        from tui import run_skill_selector
    except ImportError:
        # Try importing from same directory
        import importlib.util
        tui_path = SCRIPT_DIR / "tui.py"
        spec = importlib.util.spec_from_file_location("tui", tui_path)
        tui_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tui_module)
        run_skill_selector = tui_module.run_skill_selector

    selected_skills = run_skill_selector(skills, install_skill_from_github)

    if not selected_skills:
        print("\nNo skills selected.")
        return skills

    # Install selected skills
    print(f"\n{'='*70}")
    print(f"INSTALLING {len(selected_skills)} SKILL(S)")
    print(f"{'='*70}\n")

    success_count = 0
    fail_count = 0

    for skill in selected_skills:
        name = skill.get("name", "Unknown")
        skillsmp_url = skill.get("skillUrl", "")
        github_url = skill.get("githubUrl") or skillsmp_url_to_github(skillsmp_url)

        print(f"Installing: {name}...")

        if github_url:
            success = install_skill_from_github(github_url)
            if success:
                success_count += 1
            else:
                print(f"  Failed. Try manually: {skillsmp_url}")
                fail_count += 1
        else:
            print(f"  Couldn't determine GitHub URL. Visit: {skillsmp_url}")
            fail_count += 1
        print()

    print(f"{'='*70}")
    print(f"Installed: {success_count} | Failed: {fail_count}")
    print(f"{'='*70}")

    return skills


def cmd_setup(args):
    """Setup API key."""
    print("SkillsMP API Setup")
    print("-" * 40)
    print("Get your API key from: https://skillsmp.com/docs/api")
    print()

    api_key = input("Enter your API key: ").strip()

    if not api_key:
        print("Error: No API key provided.")
        sys.exit(1)

    # Test the API key
    print("Testing API key...", file=sys.stderr)
    result = api_request("/api/v1/skills/search?q=test&limit=1", api_key)

    if result and result.get("success"):
        save_config({"api_key": api_key})
        print(f"\nSuccess! API key saved to {CONFIG_FILE}")
    else:
        print("\nWarning: API key may be invalid, but saved anyway.")
        save_config({"api_key": api_key})


def cmd_search(args):
    """Keyword search command."""
    api_key = get_api_key()
    use_tui = getattr(args, 'tui', False)
    json_output = getattr(args, 'json', False)

    if not use_tui and not json_output:
        print(f"Searching for: '{args.query}'...\n", file=sys.stderr)

    result = search_skills(
        args.query,
        api_key,
        limit=args.limit,
        page=args.page,
        sort_by=args.sort
    )
    format_results(result, is_ai_search=False, interactive=args.interactive, use_tui=use_tui, json_output=json_output)


def cmd_ai_search(args):
    """AI semantic search command."""
    api_key = get_api_key()
    use_tui = getattr(args, 'tui', False)
    json_output = getattr(args, 'json', False)

    if not use_tui and not json_output:
        print(f"AI searching for: '{args.query}'...\n", file=sys.stderr)

    result = ai_search_skills(args.query, api_key)
    format_results(result, is_ai_search=True, interactive=args.interactive, use_tui=use_tui, json_output=json_output)


def cmd_analyze(args):
    """Analyze project and search for relevant skills."""
    api_key = get_api_key()

    print(f"Analyzing project: {args.dir}...\n", file=sys.stderr)
    analysis = analyze_project(args.dir, deep=args.deep)

    # Show what was detected
    print("=" * 70)
    print("PROJECT ANALYSIS")
    print("=" * 70)

    if analysis["technologies"]:
        print(f"\nDetected Technologies: {', '.join(analysis['technologies'])}")

    if analysis["raw_keywords"]:
        print(f"Extracted Keywords: {', '.join(list(analysis['raw_keywords'])[:15])}")

    if analysis["goals"]:
        print(f"Detected Goals:")
        for goal in analysis["goals"][:3]:
            print(f"  - {goal[:100]}")

    if analysis["context"]:
        print(f"\nCLAUDE.md Preview:")
        print(f"  {analysis['context'][:200]}...")

    # Build search query from analysis
    search_terms = []

    # Prioritize technologies
    if analysis["technologies"]:
        search_terms.extend(analysis["technologies"][:5])

    # Add keywords
    if analysis["raw_keywords"]:
        search_terms.extend(list(analysis["raw_keywords"])[:5])

    if not search_terms:
        print("\nCould not detect project context. Try manual search.")
        return

    # Perform searches
    print(f"\n{'='*70}")
    print("SEARCHING FOR RELEVANT SKILLS")
    print(f"{'='*70}")

    # Search with top technologies
    if analysis["technologies"]:
        query = " ".join(analysis["technologies"][:3])
        print(f"\nSearching by technology: '{query}'")
        result = search_skills(query, api_key, limit=5, sort_by="stars")
        format_results(result, is_ai_search=False)

    # AI search with context if we have goals
    if analysis["goals"] or analysis["context"]:
        context = analysis["goals"][0] if analysis["goals"] else analysis["context"][:200]
        print(f"\nAI searching by context: '{context[:50]}...'")
        result = ai_search_skills(context, api_key)
        format_results(result, is_ai_search=True)


def parse_github_url(url):
    """
    Parse a GitHub URL to extract owner, repo, branch, and path.

    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/tree/branch/path/to/skill
    - https://github.com/owner/repo/blob/branch/path/to/SKILL.md
    """
    parsed = urlparse(url)

    if "github.com" not in parsed.netloc:
        return None

    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2:
        return None

    result = {
        "owner": parts[0],
        "repo": parts[1],
        "branch": "main",  # default
        "path": "",
    }

    # Handle /tree/branch/path or /blob/branch/path
    if len(parts) > 3 and parts[2] in ("tree", "blob"):
        result["branch"] = parts[3]
        if len(parts) > 4:
            result["path"] = "/".join(parts[4:])
            # Remove SKILL.md from path if present
            if result["path"].endswith("SKILL.md"):
                result["path"] = "/".join(parts[4:-1])

    return result


def install_skill_from_github(url, skill_name=None, force=False):
    """
    Install a skill from a GitHub URL.

    Uses git sparse-checkout to download only the skill folder.
    """
    github_info = parse_github_url(url)

    if not github_info:
        print(f"Error: Invalid GitHub URL: {url}", file=sys.stderr)
        print("Expected format: https://github.com/owner/repo/tree/branch/path/to/skill", file=sys.stderr)
        return False

    owner = github_info["owner"]
    repo = github_info["repo"]
    branch = github_info["branch"]
    path = github_info["path"]

    # Determine skill name from path or repo
    if skill_name:
        final_name = skill_name
    elif path:
        # Use last folder in path as skill name
        final_name = path.rstrip("/").split("/")[-1]
        # Clean up the name
        final_name = re.sub(r"[^a-zA-Z0-9_-]", "-", final_name).lower()
    else:
        final_name = repo.lower()

    # Target directory
    target_dir = SKILLS_DIR / final_name

    if target_dir.exists():
        if force:
            print(f"Removing existing skill: {target_dir}")
            shutil.rmtree(target_dir)
        else:
            print(f"Error: Skill already exists: {target_dir}", file=sys.stderr)
            print("Use --force to overwrite", file=sys.stderr)
            return False

    # Ensure skills directory exists
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    repo_url = f"https://github.com/{owner}/{repo}.git"

    print(f"Installing skill '{final_name}' from {owner}/{repo}...")
    print(f"  Branch: {branch}")
    if path:
        print(f"  Path: {path}")
    print()

    # Use sparse checkout to get only the skill folder
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Initialize repo with sparse checkout
            subprocess.run(
                ["git", "clone", "--filter=blob:none", "--no-checkout", "--depth=1",
                 "--branch", branch, repo_url, tmpdir],
                check=True,
                capture_output=True,
                text=True
            )

            # Configure sparse checkout
            subprocess.run(
                ["git", "-C", tmpdir, "sparse-checkout", "init", "--cone"],
                check=True,
                capture_output=True,
                text=True
            )

            if path:
                subprocess.run(
                    ["git", "-C", tmpdir, "sparse-checkout", "set", path],
                    check=True,
                    capture_output=True,
                    text=True
                )

            # Checkout
            subprocess.run(
                ["git", "-C", tmpdir, "checkout"],
                check=True,
                capture_output=True,
                text=True
            )

            # Copy the skill folder to target
            if path:
                source = Path(tmpdir) / path
            else:
                source = Path(tmpdir)

            if not source.exists():
                print(f"Error: Path not found in repository: {path}", file=sys.stderr)
                return False

            # Check if SKILL.md exists
            skill_md = source / "SKILL.md"
            if not skill_md.exists():
                # Try to find SKILL.md in subdirectories
                found = list(source.glob("**/SKILL.md"))
                if found:
                    source = found[0].parent
                    print(f"  Found SKILL.md in: {source.relative_to(Path(tmpdir))}")
                else:
                    print(f"Warning: No SKILL.md found. Installing anyway.", file=sys.stderr)

            # Copy to target
            if source.is_dir():
                shutil.copytree(source, target_dir, dirs_exist_ok=True)
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target_dir / source.name)

            # Remove .git if copied
            git_dir = target_dir / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)

            print(f"\nSuccess! Skill installed to: {target_dir}")

            # Show skill info if available
            skill_md = target_dir / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text(encoding="utf-8")
                # Extract name and description from frontmatter
                match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
                if match:
                    frontmatter = match.group(1)
                    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
                    desc_match = re.search(r"^description:\s*[|>]?\s*\n?((?:[ \t]+.+\n?)+|.+)$", frontmatter, re.MULTILINE)

                    if name_match:
                        print(f"  Name: {name_match.group(1).strip()}")
                    if desc_match:
                        desc = desc_match.group(1).strip()[:200]
                        print(f"  Description: {desc}...")

            return True

        except subprocess.CalledProcessError as e:
            print(f"Error: Git operation failed: {e.stderr}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False


def cmd_install(args):
    """Install a skill from GitHub."""
    url = args.url

    # If it's a SkillsMP URL, inform the user
    if "skillsmp.com" in url:
        print("Note: SkillsMP URLs point to skill pages, not directly installable.", file=sys.stderr)
        print("Please find the GitHub source URL on the skill page and use that.", file=sys.stderr)
        print("\nAlternatively, provide a GitHub URL like:", file=sys.stderr)
        print("  https://github.com/owner/repo/tree/main/path/to/skill", file=sys.stderr)
        sys.exit(1)

    success = install_skill_from_github(
        url,
        skill_name=args.name,
        force=args.force
    )

    if not success:
        sys.exit(1)


def cmd_list(args):
    """List installed skills."""
    json_output = getattr(args, 'json', False)

    if not SKILLS_DIR.exists():
        if json_output:
            print(json.dumps({"skills": [], "count": 0}))
        else:
            print("No skills installed yet.")
            print(f"Skills directory: {SKILLS_DIR}")
        return

    skills = []
    for item in SKILLS_DIR.iterdir():
        if item.is_dir():
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                try:
                    content = skill_md.read_text(encoding="utf-8")
                    match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
                    name = item.name
                    desc = ""
                    if match:
                        frontmatter = match.group(1)
                        name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
                        if name_match:
                            name = name_match.group(1).strip()
                        desc_match = re.search(r"^description:\s*[|>]?\s*\n?((?:[ \t]+.+\n?)+|.+)$", frontmatter, re.MULTILINE)
                        if desc_match:
                            desc = desc_match.group(1).strip().split("\n")[0][:80]
                    skills.append((item.name, name, desc))
                except:
                    skills.append((item.name, item.name, ""))
            else:
                skills.append((item.name, item.name, "(no SKILL.md)"))

    if not skills:
        if json_output:
            print(json.dumps({"skills": [], "count": 0}))
        else:
            print("No skills installed yet.")
        return

    # JSON output for Claude
    if json_output:
        output = {
            "skills": [
                {"folder": folder, "name": name, "description": desc}
                for folder, name, desc in sorted(skills)
            ],
            "count": len(skills)
        }
        print(json.dumps(output, indent=2))
        return

    print(f"\n{'='*70}")
    print(f"Installed Skills ({len(skills)})")
    print(f"{'='*70}\n")

    for folder, name, desc in sorted(skills):
        print(f"  {folder}/")
        if name != folder:
            print(f"    Name: {name}")
        if desc:
            print(f"    {desc}")
        print()

    print(f"Skills directory: {SKILLS_DIR}")


def cmd_uninstall(args):
    """Uninstall a skill."""
    skill_name = args.skill_name
    target_dir = SKILLS_DIR / skill_name

    if not target_dir.exists():
        print(f"Error: Skill not found: {skill_name}", file=sys.stderr)
        print(f"Use 'list' command to see installed skills.", file=sys.stderr)
        sys.exit(1)

    if not args.yes:
        confirm = input(f"Remove skill '{skill_name}'? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return

    shutil.rmtree(target_dir)
    print(f"Uninstalled: {skill_name}")


def check_for_updates(skill_dir):
    """
    Check if a skill has updates available.
    Returns: (has_updates, behind_count, error_message)
    """
    git_dir = skill_dir / ".git"
    if not git_dir.exists():
        return False, 0, "Not a git repository"

    try:
        # Fetch latest from remote
        subprocess.run(
            ["git", "-C", str(skill_dir), "fetch", "--quiet"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Check how many commits behind
        result = subprocess.run(
            ["git", "-C", str(skill_dir), "rev-list", "--count", "HEAD..@{upstream}"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            behind = int(result.stdout.strip())
            return behind > 0, behind, None
        else:
            return False, 0, "Could not check upstream"

    except subprocess.TimeoutExpired:
        return False, 0, "Timeout checking for updates"
    except subprocess.CalledProcessError as e:
        return False, 0, f"Git error: {e.stderr.strip()}"
    except Exception as e:
        return False, 0, str(e)


def update_skill(skill_dir, skill_name):
    """
    Update a skill by pulling latest changes.
    Returns: (success, message)
    """
    git_dir = skill_dir / ".git"
    if not git_dir.exists():
        return False, "Not a git repository (was not installed via git clone)"

    try:
        # Check for local changes
        result = subprocess.run(
            ["git", "-C", str(skill_dir), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.stdout.strip():
            return False, "Has local changes. Commit or stash them first."

        # Pull latest
        result = subprocess.run(
            ["git", "-C", str(skill_dir), "pull", "--ff-only"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            if "Already up to date" in result.stdout:
                return True, "Already up to date"
            else:
                # Extract update info
                return True, "Updated successfully"
        else:
            return False, f"Pull failed: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return False, "Timeout during update"
    except subprocess.CalledProcessError as e:
        return False, f"Git error: {e.stderr.strip()}"
    except Exception as e:
        return False, str(e)


def cmd_update(args):
    """Check for and apply updates to skills."""
    skill_name = args.skill_name if hasattr(args, 'skill_name') and args.skill_name else None
    check_only = args.check if hasattr(args, 'check') else False
    update_all = args.all if hasattr(args, 'all') else False

    if not SKILLS_DIR.exists():
        print("No skills installed yet.")
        return

    # Determine which skills to update
    if skill_name:
        # Update specific skill
        skill_dirs = [(SKILLS_DIR / skill_name, skill_name)]
        if not skill_dirs[0][0].exists():
            print(f"Error: Skill not found: {skill_name}", file=sys.stderr)
            sys.exit(1)
    elif update_all:
        # Update all skills
        skill_dirs = [(d, d.name) for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / ".git").exists()]
    else:
        # Default: update skill-search itself
        skill_dirs = [(SCRIPT_DIR, "skill-search")]

    if not skill_dirs:
        print("No updatable skills found (skills must be installed via git clone).")
        return

    print(f"\n{'='*70}")
    print("CHECKING FOR UPDATES" if check_only else "UPDATING SKILLS")
    print(f"{'='*70}\n")

    updated_count = 0
    error_count = 0

    for skill_dir, name in skill_dirs:
        print(f"  {name}... ", end="", flush=True)

        has_updates, behind, error = check_for_updates(skill_dir)

        if error:
            print(f"[SKIP] {error}")
            continue

        if not has_updates:
            print("[UP TO DATE]")
            continue

        if check_only:
            print(f"[{behind} update(s) available]")
            updated_count += 1
        else:
            # Apply update
            success, message = update_skill(skill_dir, name)
            if success:
                print(f"[UPDATED] {message}")
                updated_count += 1
            else:
                print(f"[ERROR] {message}")
                error_count += 1

    print()
    if check_only:
        if updated_count > 0:
            print(f"{updated_count} skill(s) have updates available.")
            print("Run without --check to apply updates.")
        else:
            print("All skills are up to date.")
    else:
        if updated_count > 0:
            print(f"{updated_count} skill(s) updated.")
        if error_count > 0:
            print(f"{error_count} skill(s) had errors.")


def main():
    # Auto-check for updates (once per day, silent)
    auto_check_for_updates()

    parser = argparse.ArgumentParser(
        description="Search SkillsMP for Claude Code skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s setup                          # Configure API key
  %(prog)s search "react testing"         # Keyword search
  %(prog)s search "git" --sort stars      # Sort by popularity
  %(prog)s search "react" --json          # JSON output (for Claude)
  %(prog)s ai "improve code quality"      # AI semantic search
  %(prog)s analyze --dir /path/to/project # Analyze project
  %(prog)s install <github-url>           # Install skill from GitHub
  %(prog)s list                           # List installed skills
  %(prog)s uninstall <skill-name>         # Uninstall a skill
        """
    )

    sub = parser.add_subparsers(dest="command", help="Commands")

    # Setup command
    sub.add_parser("setup", help="Configure API key")

    # Search command
    p_search = sub.add_parser("search", help="Keyword search")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("-n", "--limit", type=int, default=10, help="Results (max 100)")
    p_search.add_argument("-p", "--page", type=int, default=1, help="Page number")
    p_search.add_argument("--sort", choices=["stars", "recent"], help="Sort order")
    p_search.add_argument("-i", "--interactive", action="store_true", help="Interactive mode: select skills to install")
    p_search.add_argument("--tui", action="store_true", help="Use TUI for multi-select skill installation")
    p_search.add_argument("--json", action="store_true", help="Output results as JSON (for Claude to parse)")

    # AI search command
    p_ai = sub.add_parser("ai", help="AI semantic search")
    p_ai.add_argument("query", help="Natural language query")
    p_ai.add_argument("-i", "--interactive", action="store_true", help="Interactive mode: select skills to install")
    p_ai.add_argument("--tui", action="store_true", help="Use TUI for multi-select skill installation")
    p_ai.add_argument("--json", action="store_true", help="Output results as JSON (for Claude to parse)")

    # Analyze command
    p_analyze = sub.add_parser("analyze", help="Analyze project for relevant skills")
    p_analyze.add_argument("--dir", default=".", help="Project directory")
    p_analyze.add_argument("--deep", action="store_true", help="Deep scan source files")

    # Install command
    p_install = sub.add_parser("install", help="Install skill from GitHub URL")
    p_install.add_argument("url", help="GitHub URL to skill folder")
    p_install.add_argument("--name", help="Custom name for the skill folder")
    p_install.add_argument("--force", action="store_true", help="Overwrite existing skill")

    # List command
    p_list = sub.add_parser("list", help="List installed skills")
    p_list.add_argument("--json", action="store_true", help="Output as JSON (for Claude to parse)")

    # Uninstall command
    p_uninstall = sub.add_parser("uninstall", help="Uninstall a skill")
    p_uninstall.add_argument("skill_name", help="Name of skill to uninstall")
    p_uninstall.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    # Update command
    p_update = sub.add_parser("update", help="Check for and apply updates")
    p_update.add_argument("skill_name", nargs="?", help="Specific skill to update (default: skill-search)")
    p_update.add_argument("--all", action="store_true", help="Update all installed skills")
    p_update.add_argument("--check", action="store_true", help="Only check for updates, don't apply")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "ai":
        cmd_ai_search(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "install":
        cmd_install(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "uninstall":
        cmd_uninstall(args)
    elif args.command == "update":
        cmd_update(args)


if __name__ == "__main__":
    main()
