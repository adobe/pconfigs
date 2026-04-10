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

RULE_METADATA: dict[str, list[str]] = {
    "policies": [
        "alwaysApply: true",
        '"Repo-wide coding policies, style rules, pconfig specialization/modification rules, and formatting conventions"',
    ],
    "pconfigs": [
        "alwaysApply: true",
        '"pconfigs library usage rules: core design, subconfigs, computed fields, config instances, environments, enums, external libraries, entrypoints, testing, and typing"',
    ],
    "naming": [
        "alwaysApply: true",
        '"Naming conventions for classes, configs, variables, functions, properties, and config fields"',
    ],
    "external_libs": [
        'globs: ["**/*.py"]',
        '"Rules for wrapping external library classes and functions with pconfigs"',
    ],
    "pproperty": [
        'globs: ["**/*.py"]',
        '"Detailed @pproperty patterns for computed config fields"',
    ],
}


def _make_frontmatter(rule_name: str) -> str:
    meta = RULE_METADATA[rule_name]
    activation_line, description = meta

    return f"---\n{activation_line}\ndescription: {description}\n---\n"


def get_shared_rules_dir() -> Path:

    return Path(__file__).parent / "cursor_assets" / "rules"


def get_shared_skills_dir() -> Path:

    return Path(__file__).parent / "cursor_assets" / "skills"


def get_installation_test_dir() -> Path:

    return Path(__file__).parent / "cursor_assets" / "installation_test"


# =============================================================================
# Subcommands
# =============================================================================


def cmd_list() -> int:
    """List all available rules and skills."""
    rules_dir = get_shared_rules_dir()
    skills_dir = get_shared_skills_dir()

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
    rules_dir = get_shared_rules_dir()
    skills_dir = get_shared_skills_dir()

    rule_path = rules_dir / f"{name}.md"
    if rule_path.exists():
        if name in RULE_METADATA:
            print(_make_frontmatter(name))

        print(rule_path.read_text())

        return 0

    skill_path = skills_dir / name / "SKILL.md"
    if skill_path.exists():
        print(skill_path.read_text())

        return 0

    print(f"Not found: {name}", file=sys.stderr)
    print("Use 'python -m pconfigs.cursor list' to see available items", file=sys.stderr)

    return 1


def cmd_path() -> int:
    """Print the path to bundled assets."""
    print(f"Rules:  {get_shared_rules_dir()}")
    print(f"Skills: {get_shared_skills_dir()}")

    return 0


def cmd_install(target_dir: str, yes: bool) -> int:
    """Install pconfigs rules and skills to target directory."""
    target = Path(target_dir).resolve()
    cursor_dir = target / ".cursor"
    rules_dest = cursor_dir / "rules" / "pconfigs"
    skills_dest = cursor_dir / "skills"

    src_rules = get_shared_rules_dir()
    src_skills = get_shared_skills_dir()

    if not yes:
        print(f"This will install pconfigs Cursor rules and skills to {cursor_dir}/")
        try:
            response = input("Continue? [y/N] ").strip().lower()
        except EOFError:
            response = ""

        if response not in ("y", "yes"):
            print("Aborted.")

            return 1

    # -------------------------------------------------------------------------
    # Step 1: Copy rules to .cursor/rules/ as .mdc files with frontmatter
    # -------------------------------------------------------------------------
    print(f"Installing rules to {rules_dest}/")

    if rules_dest.exists():
        print("  Directory exists, updating files...")
    else:
        rules_dest.mkdir(parents=True)
        print(f"  Created {rules_dest}/")

    for src_path in sorted(src_rules.glob("*.md")):
        rule_name = src_path.stem
        dest_path = rules_dest / f"{rule_name}.mdc"
        content = src_path.read_text()

        if rule_name in RULE_METADATA:
            content = _make_frontmatter(rule_name) + "\n" + content

        dest_path.write_text(content)
        print(f"  {rule_name}.mdc")

    # -------------------------------------------------------------------------
    # Step 2: Copy skills to .cursor/skills/pconfigs-*/
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
    # Step 3: Copy installation test to .cursor/installation_test/
    # -------------------------------------------------------------------------
    src_test = get_installation_test_dir()
    test_dest = cursor_dir / "installation_test"
    print(f"\nInstalling installation test to {test_dest}/")

    if test_dest.exists():
        shutil.rmtree(test_dest)

    shutil.copytree(src_test, test_dest)

    for src_path in sorted(test_dest.rglob("*")):
        if src_path.is_file():
            print(f"  {src_path.relative_to(test_dest)}")

    # -------------------------------------------------------------------------
    # Step 4: Create project environment rule if it doesn't exist
    # -------------------------------------------------------------------------
    env_rule_dest = cursor_dir / "rules" / "environment.mdc"

    if not env_rule_dest.exists():
        env_rule_content = """\
---
alwaysApply: true
description: "Project environment setup"
---

## Environment

- Conda environment: `[FILL IN: e.g., my_environment]`
- Before running any Python commands, activate the conda environment:
  ```bash
  conda activate [FILL IN: e.g., my_environment]
  ```
"""
        env_rule_dest.parent.mkdir(parents=True, exist_ok=True)
        env_rule_dest.write_text(env_rule_content)
        print(f"\nCreated {env_rule_dest}")

    print("\n" + "=" * 60)
    print("IMPORTANT: Update .cursor/rules/environment.mdc with your")
    print("project's Python environment name and activation command.")
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
        prog="python -m pconfigs.cursor",
        description="Install and manage pconfigs Cursor rules and skills",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available rules and skills")

    show_parser = subparsers.add_parser("show", help="Print a rule or skill to stdout")
    show_parser.add_argument("name", help="Rule or skill name")

    subparsers.add_parser("path", help="Print paths to bundled assets")

    subparsers.add_parser("test", help="Print instructions for running the installation test")

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
        help="Skip confirmation prompt",
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
        return cmd_install(args.target, yes=args.yes)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
