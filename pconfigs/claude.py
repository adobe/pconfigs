# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def get_assets_dir() -> Path:
    """Return the path to the bundled assets directory."""

    return Path(__file__).parent / "claude_assets"


def get_rules_dir() -> Path:

    return get_assets_dir() / "rules"


def get_skills_dir() -> Path:

    return get_assets_dir() / "skills"


def get_templates_dir() -> Path:

    return get_assets_dir() / "templates"


def get_installation_test_dir() -> Path:

    return get_assets_dir() / "installation_test"


# =============================================================================
# Subcommands
# =============================================================================


def cmd_list() -> int:
    """List all available rules and skills."""
    rules_dir = get_rules_dir()
    skills_dir = get_skills_dir()

    print("Available rules:")
    for path in sorted(rules_dir.glob("*.md")):
        print(f"  {path.stem}")

    print("\nAvailable skills:")
    for path in sorted(skills_dir.iterdir()):
        if path.is_dir() and (path / "SKILL.md").exists():
            print(f"  {path.name}")

    return 0


def cmd_show(name: str) -> int:
    """Print a rule or skill to stdout."""
    rules_dir = get_rules_dir()
    skills_dir = get_skills_dir()

    # Try rules first
    rule_path = rules_dir / f"{name}.md"
    if rule_path.exists():
        print(rule_path.read_text())

        return 0

    # Try skills
    skill_path = skills_dir / name / "SKILL.md"
    if skill_path.exists():
        print(skill_path.read_text())

        return 0

    print(f"Not found: {name}", file=sys.stderr)
    print("Use 'python -m pconfigs.claude list' to see available items", file=sys.stderr)

    return 1


def cmd_path() -> int:
    """Print the path to bundled assets."""
    print(f"Rules:  {get_rules_dir()}")
    print(f"Skills: {get_skills_dir()}")

    return 0


def cmd_install(target_dir: str, yes: bool) -> int:
    """Install pconfigs rules and skills to target directory."""
    target = Path(target_dir).resolve()
    claude_dir = target / ".claude"
    rules_dest = claude_dir / "pconfigs"
    skills_dest = claude_dir / "skills"
    claude_md = target / "CLAUDE.md"

    src_rules = get_rules_dir()
    src_skills = get_skills_dir()

    # -------------------------------------------------------------------------
    # Step 1: Copy rules to .claude/pconfigs/
    # -------------------------------------------------------------------------
    print(f"Installing rules to {rules_dest}/")

    if rules_dest.exists():
        print("  Directory exists, updating files...")
    else:
        rules_dest.mkdir(parents=True)
        print(f"  Created {rules_dest}/")

    for src_path in sorted(src_rules.glob("*.md")):
        dest_path = rules_dest / src_path.name
        shutil.copy2(src_path, dest_path)
        print(f"  {src_path.name}")

    # -------------------------------------------------------------------------
    # Step 2: Copy skills to .claude/skills/pconfigs-*/
    # -------------------------------------------------------------------------
    print(f"\nInstalling skills to {skills_dest}/")

    skills_dest.mkdir(parents=True, exist_ok=True)

    for src_skill in sorted(src_skills.iterdir()):
        if not src_skill.is_dir():
            continue

        skill_md = src_skill / "SKILL.md"
        if not skill_md.exists():
            continue

        dest_skill = skills_dest / src_skill.name
        dest_skill.mkdir(exist_ok=True)
        shutil.copy2(skill_md, dest_skill / "SKILL.md")
        print(f"  {src_skill.name}/SKILL.md")

    # -------------------------------------------------------------------------
    # Step 3: Copy installation test to .claude/installation_test/
    # -------------------------------------------------------------------------
    src_test = get_installation_test_dir()
    test_dest = claude_dir / "installation_test"
    print(f"\nInstalling installation test to {test_dest}/")

    if test_dest.exists():
        shutil.rmtree(test_dest)

    shutil.copytree(src_test, test_dest)

    for src_path in sorted(test_dest.rglob("*")):
        if src_path.is_file():
            print(f"  {src_path.relative_to(test_dest)}")

    # -------------------------------------------------------------------------
    # Step 4: Update CLAUDE.md
    # -------------------------------------------------------------------------
    print()

    imports_to_add = [
        "@.claude/pconfigs/policies.md",
        "@.claude/pconfigs/pconfigs.md",
        "@.claude/pconfigs/naming.md",
        "@.claude/pconfigs/external_libs.md",
        "@.claude/pconfigs/pproperty.md",
    ]

    if claude_md.exists():
        existing_content = claude_md.read_text()
        existing_lines = set(existing_content.splitlines())

        # Filter out imports that already exist
        new_imports = [imp for imp in imports_to_add if imp not in existing_lines]

        if not new_imports:
            print("CLAUDE.md already has all pconfigs imports.")

            return 0

        print("Append to CLAUDE.md:\n")
        for imp in new_imports:
            print(f"  {imp}")
        print()

        if not yes:
            response = input("Append these imports? [y/n]: ").strip().lower()
            if response != "y":
                print("Skipped CLAUDE.md update.")

                return 0

        # Append imports
        with open(claude_md, "a") as f:
            f.write("\n")
            for imp in new_imports:
                f.write(f"{imp}\n")

        print("Updated CLAUDE.md")

    else:
        print("No CLAUDE.md found. Create one?\n")

        template_content = """\
# Project Rules

@.claude/pconfigs/policies.md
@.claude/pconfigs/pconfigs.md
@.claude/pconfigs/naming.md
@.claude/pconfigs/external_libs.md
@.claude/pconfigs/pproperty.md

## Environment

- Python environment: `[FILL IN: e.g., myproject]`
- Activation: `[FILL IN: e.g., conda activate myproject]`
"""

        print("--- CLAUDE.md content ---")
        print(template_content)
        print("-------------------------\n")

        if not yes:
            response = input("Create this file? [y/n]: ").strip().lower()
            if response != "y":
                print("Skipped CLAUDE.md creation.")

                return 0

        claude_md.write_text(template_content)
        print(f"Created {claude_md}")

    # -------------------------------------------------------------------------
    # Step 5: Reminder
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("IMPORTANT: Update the Environment section in your CLAUDE.md")
    print("with your project's Python environment activation command.")
    print("=" * 60)

    return 0


def cmd_test() -> int:
    """Print instructions for running the installation test."""
    instructions_path = get_installation_test_dir() / "INSTRUCTIONS.md"
    print(instructions_path.read_text())

    return 0


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m pconfigs.claude",
        description="Install and manage pconfigs Claude Code rules and skills",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="List available rules and skills")

    # show
    show_parser = subparsers.add_parser("show", help="Print a rule or skill to stdout")
    show_parser.add_argument("name", help="Rule or skill name")

    # path
    subparsers.add_parser("path", help="Print paths to bundled assets")

    # test
    subparsers.add_parser("test", help="Print instructions for running the installation test")

    # install
    install_parser = subparsers.add_parser(
        "install",
        help="Install rules and skills to a project directory",
    )
    install_parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target project directory (default: current directory)",
    )
    install_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompts",
    )

    args = parser.parse_args()

    if args.command == "list":
        return cmd_list()

    elif args.command == "show":
        return cmd_show(args.name)

    elif args.command == "path":
        return cmd_path()

    elif args.command == "test":
        return cmd_test()

    elif args.command == "install":
        return cmd_install(args.target, args.yes)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
