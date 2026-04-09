# Claude

`pconfigs` includes a tool to install Claude rules and skills into your project. These rules teach Claude how to write pconfigs code. Users may wish to modify some coding conventions by copying and customizing the rules.

## Installation

Install the rules and skills to your project:

```console
$ python -m pconfigs.claude install
```

Pass `-y` to skip confirmation prompts (useful in scripts):

```console
$ python -m pconfigs.claude install -y
```

This creates:
- `.claude/pconfigs/` — Rule files that teach Claude pconfigs conventions
- `.claude/skills/pconfigs-*/` — Skills for printing and testing configs
- `.claude/installation_test/` — Test suite to verify rule installation
- `CLAUDE.md` — Entry point that imports the rules (created if it doesn't exist)

### Configure your environment

After installation, update the Environment section in your `CLAUDE.md` with your project's Python environment:

```markdown
## Environment

- Python environment: `my_project`
- Activation: `conda activate my_project`
```

This tells Claude how to run pconfigs commands in your project.

To install to a different directory, pass the path: `python -m pconfigs.claude install /path/to/project`.

## Installation test

The installer includes a test suite to verify the agent has learned the rules correctly. Run the test in two conversations:

1. **Conversation A** — send: `Take the test. @.claude/installation_test/INSTRUCTIONS.md`
2. **Conversation B** — send: `Score the test. @.claude/installation_test/INSTRUCTIONS.md`
3. Open `TEST_SCORE.md` to review.

To re-run the test, delete the `answers/`, `scores/`, and `TEST_SCORE.md` from `.claude/installation_test/` and re-run the installer to restore the test files.

## What gets installed

### Rules

The installer copies these rule files to `.claude/pconfigs/`:

| File | Description |
|------|-------------|
| `policies.md` | Repo-wide coding policies and pconfig modification rules |
| `pconfigs.md` | Core pconfigs usage patterns and conventions |
| `naming.md` | Naming conventions for classes, configs, and variables |
| `external_libs.md` | Rules for wrapping external libraries |
| `pproperty.md` | Patterns for computed config fields |

### Skills

The installer creates these skill directories in `.claude/skills/`:

| Skill | Description |
|-------|-------------|
| `pconfigs-print` | Print resolved config values with `/pconfigs-print <dotpath>` |
| `pconfigs-test` | Test pconfig files with `/pconfigs-test [dotpath]` |

## Other commands

### List available rules and skills

```console
$ python -m pconfigs.claude list
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
$ python -m pconfigs.claude show pconfigs
$ python -m pconfigs.claude show pconfigs-print
```

### Print paths to bundled assets

```console
$ python -m pconfigs.claude path
Rules:  /path/to/site-packages/pconfigs/claude_assets/rules
Skills: /path/to/site-packages/pconfigs/claude_assets/skills
```

## Existing projects

When your project already has a `CLAUDE.md`, the installer:
1. Copies rule files to `.claude/pconfigs/` (overwrites if they exist)
2. Copies skill files to `.claude/skills/pconfigs-*/`
3. Appends missing `@.claude/pconfigs/...` imports to `CLAUDE.md`

The installer detects existing imports and won't add duplicates.

## Manual installation

If you prefer not to use the installer, you can manually:

1. Copy rules from the package location (`python -m pconfigs.claude path`)
2. Add imports to your `CLAUDE.md`:

```markdown
@.claude/pconfigs/policies.md
@.claude/pconfigs/pconfigs.md
@.claude/pconfigs/naming.md
@.claude/pconfigs/external_libs.md
@.claude/pconfigs/pproperty.md
```
