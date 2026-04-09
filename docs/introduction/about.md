# About

## Abstract

This page provides additional background and comparisons for `pconfigs`. For the canonical high-level motivation and overview, start on the [documentation homepage](../index).

## Technical TL;DR

- **You build the whole system in Python**: A `pconfigs` config is a Python dataclass instance that names the pieces of your system and their settings (often by nesting smaller configs).
- **You stop threading options throughout your code**: Your classes read settings from `self.config`, so call sites don’t grow long lists of optional keyword arguments ([Construction](../examples/construction)).
- **You can print what will run before you run it**: `repr(config)` or `pconfigs.print` prints the fully resolved config fields as readable Python that’s easy to diff in code review ([Printing](../examples/printing)).
- **You can compute config fields with real Python**: Use `@pproperty` and `pinputs()` to compute complex derived values (even whole sub-configs) while still keeping the user’s original inputs visible; use `Pinned[...]` / `Pin(...)` to mark fields users must not set ([Properties](../examples/properties)).
- **You make new experiments by copying and changing a few lines**: Create a new Python config file, copy a base config, and override only the fields you want to change ([Quickstart](quickstart)).
- **You can test lots of configs the same way**: Use `ptest` to import and construct a whole tree of config files, so refactors don’t silently break old experiments ([Testing](../examples/testing)).

## Design principles

Experiments and systems should be:

1. **Reproducible**: A single, no-parameter command should reproduce a result ([Runnables](../examples/runnables)).
2. **Controlled**: Creating new experiments should not break old experiments (specialize prior configs instead of rewriting them).
3. **Extensible**: It should be possible to modify any part of an existing system ([Subconfigs](../patterns/subconfigs)).
4. **Transparent**: It should be clear what code does just by reading it ([Printing](../examples/printing)).
5. **Comparable**: It should be easy to compare prior experiments in new ways (diff printed configs and derived experiment files).

## Comparison to other configuration systems

### Gin configs

(TL;DR) Practical guidance:

- Choose **Gin** when you want a lightweight way to bind values to callables.
- Choose **`pconfigs`** when you want the experiment/system to be a typed, executable object with standardized running, printing/diffing, and testing workflows.

Key takeaways (high-level):

- **Global injection vs explicit scope**: Gin often sets values globally (load order matters); `pconfigs` keeps values in the config object you build.
- **Refactors**: `pconfigs` uses normal Python names and fields, so IDE renames/find-references work well; Gin uses string keys, so refactors need more care.
- **Built-in workflows**: `pconfigs` is built around printing, computed fields, and config-tree tests; Gin can support similar habits, but they are not the default workflow.

The table below summarizes common workflow differences.

| Capability | `pconfigs` | Gin |
|---|---|---|
| **Run an experiment with one standard command** (the config fully specifies what runs) | **Built in**: `python -m pconfigs.run dot.path.to.config.attr` ([Quickstart](quickstart), [Running](../examples/runnables)) | **No standard command**: you typically run your program and load one or more `.gin` files/overrides |
| **Print one file you can diff in review** (naming types/functions via imports) | **Built in**: `repr(config)` / `python -m pconfigs.print ...` prints readable Python with fully qualified imports, formatted for diffs ([Printing](../examples/printing)) | **Not the main artifact**: Gin can dump an operative config, but it is not designed around producing a single import-explicit Python file for review diffs |
| **Make “where a value lives” obvious** | Values live on a nested config object (subconfigs, typed fields) | Values are often global bindings; which value applies can depend on loaded files and override order |
| **Keep runtime call sites simple** (avoid optional kwargs everywhere) | A common pattern is “read from `self.config`” (`@pconfiged` + `@pconfig`) ([Quickstart](quickstart), [Construction](../examples/construction)) | Not a goal: Gin is great at binding optional kwargs, so call sites often still follow that style |
| **Leverage standard IDE refactors** (rename, find references) for config wiring | **Strong**: wiring uses Python symbols and typed fields | **Weaker by default**: configs are largely string-keyed selectors/bindings; refactors require extra discipline/tooling |
| **Mark fields users can’t set** | **Built in**: `Pinned[...]` / `Pin(...)` with enforcement and visibility in printed configs ([Properties](../examples/properties), [Subconfigs](../patterns/subconfigs)) | No built-in equivalent: you document and enforce conventions in code |
| **Compute fields while keeping user inputs visible** | **Built in**: `@pproperty` + `pinputs()` ([Properties](../examples/properties)) | Limited in `.gin` files: you mostly tie/reference values; for real computation you usually write Python helper/configurable functions, and you don’t get a built-in “user input vs derived value” split |
| **Model environment variables as typed config** | **Built in**: `@penv` + printable env config ([Environments](../examples/environments)) | Possible, but usually ad hoc (`os.environ` + custom helpers) |
| **Test a whole tree of configs** | **Built in**: `__pconfigs__.py` sentinels + `pconfigs.test` / `ptest` ([Testing](../examples/testing)) | No built-in convention: teams can add tests, but Gin doesn’t prescribe this workflow |
| **Configure external libraries without editing them** | **Built in**: `@pconfig(calls=...)`, `@pconfig(mocks=...)` ([External Libraries](../external_libraries/about)) | Often requires editing/annotating code (`@gin.configurable`) or writing wrappers; not always possible for third-party libraries |
| **Design around readable printed configs** | A design goal (e.g., `@penum`, printing-friendly patterns) ([Enums](../examples/enums), [External Libraries](../external_libraries/classes)) | Not a core goal: Gin optimizes for runtime injection, not for a canonical printed artifact |

## About the authors

The `pconfigs` library is a spin-off from tools that were developed for Adobe's *reflection removal* feature in **Marc Levoy**'s group, and was developed by **Eric Kee** and **Adam Pikielny**. Today, `pconfigs` is used to train Adobe's production reflection removal models that run in ACR, Lightroom, and Photoshop. These production configs have scaled beyond 20,000 lines of [*Black*](https://black.readthedocs.io/en/stable/)-formatted config: they describe the complete training process, from dataset synthesis to the learning rate scheduler and validation metrics. We hope `pconfigs` could be useful for others as well.
