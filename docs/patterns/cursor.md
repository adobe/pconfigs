# Cursor

`pconfigs` includes a tool to install Cursor rules and skills into your project. These rules teach Cursor how to write pconfigs code. Users may wish to modify some coding conventions by copying and customizing the rules.

## Installation

Install the rules and skills to your project:

```console
$ python -m pconfigs.cursor install
```

Pass `-y` to skip confirmation prompts (useful in scripts):

```console
$ python -m pconfigs.cursor install -y
```

This creates:
- `.cursor/rules/pconfigs/` — Rule files (`.mdc`) that teach Cursor pconfigs conventions
- `.cursor/rules/environment.mdc` — Project environment configuration (with `[FILL IN]` placeholders)
- `.cursor/skills/pconfigs-*/` — Skills for printing and testing configs
- `.cursor/installation_test/` — Test suite to verify rule installation

### Configure your environment

After installation, open `.cursor/rules/environment.mdc` and replace the `[FILL IN]` placeholders with your project's conda environment name:

````markdown
- Conda environment: `my_project`
- Before running any Python commands, activate the conda environment:
  ```bash
  conda activate my_project
  ```
````

This tells Cursor how to run pconfigs commands in your project. Since `environment.mdc` has `alwaysApply: true`, the environment information will be available in every conversation.

To install to a different directory, pass the path: `python -m pconfigs.cursor install /path/to/project`.

## Installation test

The installer includes a test suite to verify the agent has learned the rules correctly. Run the test in two conversations:

1. **Conversation A** — send: `Take the test. @.cursor/installation_test/INSTRUCTIONS.md`
2. **Conversation B** — send: `Score the test. @.cursor/installation_test/INSTRUCTIONS.md`
3. Open `TEST_SCORE.md` to review.

To re-run the test, delete the `answers/`, `scores/`, and `TEST_SCORE.md` from `.cursor/installation_test/` and re-run the installer to restore the test files.

## What gets installed

### Rules

The installer copies these rule files to `.cursor/rules/pconfigs/` as `.mdc` files with Cursor-specific frontmatter:

| File | Activation | Description |
|------|------------|-------------|
| `policies.mdc` | Always apply | Repo-wide coding policies and pconfig modification rules |
| `pconfigs.mdc` | Always apply | Core pconfigs usage patterns and conventions |
| `naming.mdc` | Always apply | Naming conventions for classes, configs, and variables |
| `external_libs.mdc` | `**/*.py` globs | Rules for wrapping external libraries |
| `pproperty.mdc` | `**/*.py` globs | Patterns for computed config fields |

The installer also creates `.cursor/rules/environment.mdc` (project-specific, not under `pconfigs/`) with `[FILL IN]` placeholders for your conda environment.

Rules with `alwaysApply: true` are active in every conversation. Rules with `globs` are active only when matching files are open.

### Skills

The installer creates these skill directories in `.cursor/skills/`:

| Skill | Description |
|-------|-------------|
| `pconfigs-print` | Print resolved config values |
| `pconfigs-test` | Test pconfig files |

## Differences from Claude

Cursor and Claude use the same underlying rule and skill content, but the installation layout differs:

| | Cursor | Claude |
|---|--------|-------------|
| Command | `python -m pconfigs.cursor` | `python -m pconfigs.claude` |
| Rules location | `.cursor/rules/pconfigs/` | `.claude/pconfigs/` |
| Rule format | `.mdc` with frontmatter | `.md` |
| Rule activation | Frontmatter (`alwaysApply`, `globs`) | `CLAUDE.md` imports |
| Entry point | None needed | `CLAUDE.md` |
| Skills location | `.cursor/skills/pconfigs-*/` | `.claude/skills/pconfigs-*/` |

## Other commands

### List available rules and skills

```console
$ python -m pconfigs.cursor list
Available rules:
  external_libs
  naming
  pconfigs
  policies
  pproperty

Available skills:
  pconfigs-print
  pconfigs-test
```

### View a specific rule or skill

```console
$ python -m pconfigs.cursor show pconfigs
$ python -m pconfigs.cursor show pconfigs-print
```

### Print paths to bundled assets

```console
$ python -m pconfigs.cursor path
Rules:  /path/to/site-packages/pconfigs/cursor_assets/rules
Skills: /path/to/site-packages/pconfigs/cursor_assets/skills
```

## Existing projects

When your project already has `.cursor/rules/pconfigs/`, the installer overwrites existing pconfigs rule files and leaves other rules untouched. The `environment.mdc` file is only created if it doesn't already exist, so re-running the installer won't overwrite your environment configuration.

## Manual installation

If you prefer not to use the installer, you can manually:

1. Copy rules from the package location (`python -m pconfigs.cursor path`)
2. Rename each `.md` file to `.mdc` and add the appropriate frontmatter (see `python -m pconfigs.cursor show <name>` for the expected format)
3. Place them in `.cursor/rules/pconfigs/`
