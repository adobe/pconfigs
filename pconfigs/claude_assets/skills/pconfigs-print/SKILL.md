---
description: Print resolved pconfigs config values
user-invocable: true
---

# pconfigs-print

Print the resolved value of a pconfigs config file.

## Usage

/pconfigs-print <dotpath>

## Instructions

1. Ensure the project's Python environment is active (see CLAUDE.md Environment section)
2. Run the print command:
   ```bash
   python -m pconfigs.print <dotpath> > /tmp/config.py
   ```
3. Search for the requested field:
   ```bash
   grep -A 10 "<field_name>" /tmp/config.py
   ```
4. Report the resolved value to the user

## Important

- NEVER read pconfig source files to determine config values
- The print output can exceed 10,000 lines - always grep, never read fully
- Printing can be slow for large configs, so grep the same printout multiple times to read values before re-printing to inspect changes
- Config values are computed at construction time from defaults, pproperties, and inheritance
- The dotpath format is `module.path.to.file.config_name` where `config_name` is the variable name (usually `config`)
