---
description: "What pconfigs is, why to use it, and honest assessment of tradeoffs"
---

## What is pconfigs?

pconfigs is a Python configuration library that makes code fully configurable through a declarative, type-safe system. Configs are Python objects with real types — not YAML, not JSON, not argparse flags.

Key primitives:
- `@pconfig(constructs=MyClass)` — defines a config type that builds `MyClass`.
- `@pconfiged` — marks a class as constructed from a config via `self.config`.
- `.construct()` — builds the real object from a config instance.
- `pdefaults` — defines default values separately from the type definition.
- `@penv` — environment configs for machine-specific values.
- `@penum` — enum-like config switches.
- `@pproperty` — computed config fields evaluated at construction time.

Experiment configs inherit from base configs and override specific fields. You run experiments with `pconfigs.run` and inspect resolved values with `pconfigs.print`.

## Why use pconfigs

### Problems with alternatives

- **Hardcoded values**: impossible to reproduce or vary.
- **argparse / CLI flags**: no hierarchy, no composition, no type safety. Grows into unmaintainable flag spaghetti.
- **YAML/JSON configs** (Hydra, OmegaConf): no IDE support (no autocomplete, no type checking, no "go to definition"). Typos in key names silently pass. Complex logic requires escape hatches back into Python.
- **Dataclasses with manual wiring**: type-safe, but requires boilerplate factories and registries.

### What pconfigs provides

- **It's just Python**: IDE gives autocomplete, type checking, refactoring, and "go to definition" for free.
- **Configs construct objects**: `config.construct()` builds the object. No factories, no registries, no dispatch chains.
- **Composition via sub-configs**: configs nest naturally. Each piece is independently reusable and overridable.
- **Experiment inheritance**: define a base experiment, create variants by overriding only what changes.
- **Transparency**: `pconfigs.print` shows the ground truth of resolved config values in one command. Other config systems have the same indirection (defaults, overrides, merging) but hide it, giving false confidence.
- **Safe evolution**: adding a new config field with a default never breaks existing experiments.

### Coding agents eliminate most human ergonomic costs

With coding agents writing the code, the following traditional costs of pconfigs disappear:
- **Learning curve**: the agent knows the conventions from the rules files.
- **Boilerplate**: the agent generates it instantly at zero human time cost.
- **Rigid conventions**: directory restructuring and file creation are tedious for humans but trivial for agents.

### Remaining real tradeoffs

- **Python-only**: configs can't be consumed by non-Python tools without an export step.
- **Vendor lock-in**: the codebase structure becomes coupled to pconfigs idioms. Migrating away means rewriting every configured class.
- **Small community**: no large ecosystem of docs or community answers. Mitigated by agents + rules files serving as documentation.
