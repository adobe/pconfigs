---
description: Test pconfigs files for import/construction errors
user-invocable: true
---

# pconfigs-test

Test pconfigs files to verify they import and construct without errors.

## Usage

/pconfigs-test [dotpath]

## Instructions

Ensure the project's Python environment is active first (see CLAUDE.md Environment section).

If a specific dotpath is provided, test that single module:
```bash
python -m <dotpath>
```

To test all pconfigs in the repository:
```bash
ptest
```

## Testing sub-configured objects locally

When an experiment config contains sub-configured objects that implement lightweight functionality (no GPU required, no remote platform required, no large model training/inference), it is valid to test them locally by:
1. Importing the experiment config module
2. Accessing the relevant sub-config(s) from the experiment config
3. Constructing the object(s)
4. Exercising the behavior needed for testing (call methods, iterate, check outputs, etc.)

This is appropriate when the context makes it clear the object can run on a laptop (e.g., small dataset wrappers, data transforms, utility classes).

Conversely, sub-configured objects that train or run ML models generally must be tested on the intended cloud/GPU environment rather than via local "construct and exercise" tests.

## Test workflow

1. Make code changes
2. Test the specific pconfig file you modified: `python -m dotpath.to.module`
3. If that passes, run `ptest` to verify no regressions
4. Optionally, use `pconfigs.print` to inspect the full configuration and verify parameter values
5. Fix any failures before committing

## Verifying config-construction fixes

When fixing a bug in config construction code (e.g., a pproperty that drops user overrides or uses the wrong type), verify that existing experiment configs produce identical output before and after the fix:
1. Print the affected experiment config to a file: `python -m pconfigs.print dotpath.to.experiment.config > /tmp/config_new.py`
2. Stash changes: `git stash`
3. Print again from the original code: `python -m pconfigs.print dotpath.to.experiment.config > /tmp/config_old.py`
4. Restore changes: `git stash pop`
5. Diff the two files: `diff /tmp/config_old.py /tmp/config_new.py`
6. The only acceptable differences are non-deterministic values: temp directory paths, timestamps, and set iteration order. Any change to a config parameter value means the fix has broken an existing experiment.

## Important

- A successful test means the config imports and constructs without errors
- It does NOT validate that the config produces correct behavior at runtime
- Always run `ptest` after making changes to pconfig modules to check for regressions
- The `ptest` command discovers pconfigs by looking for `__pconfigs__.py` sentinel files
