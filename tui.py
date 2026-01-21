#!/usr/bin/env python3
"""
TUI (Text User Interface) for skill-search.
Provides an interactive interface for browsing and selecting skills to install.
"""

import curses
import sys
from typing import List, Dict, Callable, Optional


class SkillSelectorTUI:
    """Interactive TUI for selecting skills to install."""

    def __init__(self, skills: List[Dict], install_callback: Callable):
        """
        Initialize the TUI.

        Args:
            skills: List of skill dictionaries with name, author, stars, description, skillUrl
            install_callback: Function to call for installing a skill (takes github_url)
        """
        self.skills = skills
        self.install_callback = install_callback
        self.selected = set()  # Indices of selected skills
        self.cursor = 0  # Current cursor position
        self.scroll_offset = 0  # For scrolling
        self.message = ""  # Status message
        self.running = True

    def run(self) -> List[Dict]:
        """Run the TUI and return selected skills."""
        if not self.skills:
            print("No skills to display.")
            return []

        try:
            return curses.wrapper(self._main)
        except curses.error as e:
            print(f"TUI error: {e}")
            print("Falling back to simple selection mode...")
            return self._fallback_selection()

    def _fallback_selection(self) -> List[Dict]:
        """Fallback for terminals that don't support curses."""
        print("\n" + "=" * 70)
        print("SKILL SELECTION (fallback mode)")
        print("=" * 70 + "\n")

        for i, skill in enumerate(self.skills):
            print(f"{i + 1}. {skill.get('name', 'Unknown')} ({skill.get('author', 'Unknown')}) - {skill.get('stars', 0)} stars")

        print("\nEnter skill numbers to install (comma-separated), or 'q' to cancel:")
        choice = input("> ").strip()

        if choice.lower() in ('q', 'quit', ''):
            return []

        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            return [self.skills[i] for i in indices if 0 <= i < len(self.skills)]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return []

    def _main(self, stdscr) -> List[Dict]:
        """Main curses loop."""
        # Setup
        curses.curs_set(0)  # Hide cursor
        curses.use_default_colors()

        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)    # Selected row
        curses.init_pair(2, curses.COLOR_GREEN, -1)                    # Checked items
        curses.init_pair(3, curses.COLOR_YELLOW, -1)                   # Stars
        curses.init_pair(4, curses.COLOR_CYAN, -1)                     # Header
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)   # Install button
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_RED)     # Cancel button
        curses.init_pair(7, curses.COLOR_MAGENTA, -1)                  # Author

        while self.running:
            self._draw(stdscr)
            self._handle_input(stdscr)

        # Return selected skills
        return [self.skills[i] for i in sorted(self.selected)]

    def _draw(self, stdscr):
        """Draw the TUI."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Reserve space for header (3 lines) and footer (4 lines)
        header_height = 3
        footer_height = 4
        list_height = height - header_height - footer_height

        # Draw header
        title = "═══ SKILL SEARCH - Select skills to install ═══"
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(0, max(0, (width - len(title)) // 2), title[:width-1])
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

        instructions = "↑/↓: Navigate | SPACE: Select | a: Select All | n: None | ENTER: Install | q: Cancel"
        stdscr.addstr(1, max(0, (width - len(instructions)) // 2), instructions[:width-1])

        selected_text = f"Selected: {len(self.selected)} / {len(self.skills)}"
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(2, max(0, (width - len(selected_text)) // 2), selected_text[:width-1])
        stdscr.attroff(curses.color_pair(2))

        # Calculate visible range
        if self.cursor < self.scroll_offset:
            self.scroll_offset = self.cursor
        elif self.cursor >= self.scroll_offset + list_height:
            self.scroll_offset = self.cursor - list_height + 1

        # Draw skill list
        for i in range(list_height):
            skill_idx = self.scroll_offset + i
            if skill_idx >= len(self.skills):
                break

            skill = self.skills[skill_idx]
            y = header_height + i

            # Check if this row is selected (cursor) or checked
            is_cursor = (skill_idx == self.cursor)
            is_checked = (skill_idx in self.selected)

            # Build the line
            checkbox = "[✓]" if is_checked else "[ ]"
            name = skill.get("name", "Unknown")[:25].ljust(25)
            author = skill.get("author", "Unknown")[:15].ljust(15)
            stars = str(skill.get("stars", 0))[:8].ljust(8)

            # Calculate remaining space for description
            prefix_len = len(checkbox) + 1 + len(name) + 1 + len(author) + 1 + len(stars) + 1
            desc_width = max(10, width - prefix_len - 2)
            desc = skill.get("description", "")[:desc_width]

            line = f"{checkbox} {name} {author} {stars} {desc}"

            # Apply styling
            if is_cursor:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, 0, line[:width-1].ljust(width-1))
                stdscr.attroff(curses.color_pair(1))
            else:
                # Draw with colors
                x = 0

                # Checkbox
                if is_checked:
                    stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(y, x, checkbox)
                if is_checked:
                    stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
                x += len(checkbox) + 1

                # Name
                stdscr.addstr(y, x, name)
                x += len(name) + 1

                # Author
                stdscr.attron(curses.color_pair(7))
                stdscr.addstr(y, x, author)
                stdscr.attroff(curses.color_pair(7))
                x += len(author) + 1

                # Stars
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, x, stars)
                stdscr.attroff(curses.color_pair(3))
                x += len(stars) + 1

                # Description
                if x < width - 1:
                    stdscr.addstr(y, x, desc[:width-x-1])

        # Draw scrollbar if needed
        if len(self.skills) > list_height:
            scrollbar_height = max(1, int(list_height * list_height / len(self.skills)))
            scrollbar_pos = int(self.scroll_offset * (list_height - scrollbar_height) / max(1, len(self.skills) - list_height))
            for i in range(list_height):
                char = "█" if scrollbar_pos <= i < scrollbar_pos + scrollbar_height else "│"
                try:
                    stdscr.addstr(header_height + i, width - 1, char)
                except curses.error:
                    pass

        # Draw footer
        footer_y = height - footer_height

        # Separator
        stdscr.addstr(footer_y, 0, "─" * (width - 1))

        # Buttons
        button_y = footer_y + 1

        if len(self.selected) > 0:
            install_text = f" INSTALL ({len(self.selected)}) "
            stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
            stdscr.addstr(button_y, 2, install_text)
            stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)

            stdscr.addstr(button_y, 2 + len(install_text) + 2, "Press ENTER to install selected skills")
        else:
            stdscr.addstr(button_y, 2, "Select skills with SPACE, then press ENTER to install")

        cancel_text = " CANCEL (q) "
        stdscr.attron(curses.color_pair(6))
        stdscr.addstr(button_y + 1, 2, cancel_text)
        stdscr.attroff(curses.color_pair(6))

        # Message line
        if self.message:
            stdscr.addstr(button_y + 2, 2, self.message[:width-4])

        stdscr.refresh()

    def _handle_input(self, stdscr):
        """Handle keyboard input."""
        key = stdscr.getch()

        if key == curses.KEY_UP or key == ord('k'):
            # Move cursor up
            if self.cursor > 0:
                self.cursor -= 1
            self.message = ""

        elif key == curses.KEY_DOWN or key == ord('j'):
            # Move cursor down
            if self.cursor < len(self.skills) - 1:
                self.cursor += 1
            self.message = ""

        elif key == ord(' '):
            # Toggle selection
            if self.cursor in self.selected:
                self.selected.remove(self.cursor)
                self.message = f"Deselected: {self.skills[self.cursor].get('name', 'Unknown')}"
            else:
                self.selected.add(self.cursor)
                self.message = f"Selected: {self.skills[self.cursor].get('name', 'Unknown')}"

        elif key == ord('a'):
            # Select all
            self.selected = set(range(len(self.skills)))
            self.message = f"Selected all {len(self.skills)} skills"

        elif key == ord('n'):
            # Select none
            self.selected.clear()
            self.message = "Cleared selection"

        elif key == ord('\n') or key == curses.KEY_ENTER or key == 10 or key == 13:
            # Confirm selection
            if self.selected:
                self.running = False
            else:
                self.message = "No skills selected. Press SPACE to select skills."

        elif key == ord('q') or key == 27:  # q or ESC
            # Cancel
            self.selected.clear()
            self.running = False

        elif key == curses.KEY_PPAGE:
            # Page up
            self.cursor = max(0, self.cursor - 10)
            self.message = ""

        elif key == curses.KEY_NPAGE:
            # Page down
            self.cursor = min(len(self.skills) - 1, self.cursor + 10)
            self.message = ""

        elif key == curses.KEY_HOME:
            # Go to top
            self.cursor = 0
            self.scroll_offset = 0
            self.message = ""

        elif key == curses.KEY_END:
            # Go to bottom
            self.cursor = len(self.skills) - 1
            self.message = ""


def run_skill_selector(skills: List[Dict], install_callback: Callable) -> List[Dict]:
    """
    Run the skill selector TUI.

    Args:
        skills: List of skill dictionaries
        install_callback: Function to install a skill

    Returns:
        List of selected skill dictionaries
    """
    if not skills:
        print("No skills to select.")
        return []

    tui = SkillSelectorTUI(skills, install_callback)
    return tui.run()


if __name__ == "__main__":
    # Test with sample data
    sample_skills = [
        {"name": "react-testing", "author": "vercel", "stars": 15000, "description": "React testing best practices", "skillUrl": "https://example.com"},
        {"name": "prisma-guide", "author": "prisma", "stars": 12000, "description": "Prisma ORM patterns", "skillUrl": "https://example.com"},
        {"name": "nextjs-perf", "author": "vercel", "stars": 8000, "description": "Next.js performance optimization", "skillUrl": "https://example.com"},
    ]

    def mock_install(url):
        print(f"Would install: {url}")
        return True

    selected = run_skill_selector(sample_skills, mock_install)
    print(f"\nSelected {len(selected)} skills:")
    for s in selected:
        print(f"  - {s['name']}")
