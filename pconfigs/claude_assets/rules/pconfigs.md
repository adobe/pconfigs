---
description: "pconfigs library usage rules: core design, subconfigs, computed fields, config instances, environments, enums, external libraries, entrypoints, testing, and typing"
---

## pconfigs usage

You are generating code for a codebase that uses the **pconfigs** library. Follow these conventions strictly.

### Core design rules (non-negotiable)

- All code must be configurable. Never hardcode behavior that a user might want to change. If a value cannot be set at config construction time (e.g., because it must be checked before imports), use an environment variable and document it in the appropriate `@penv` class.
- Add `from __future__ import annotations` only to modules that need forward references (typically pconfigs-heavy modules where config types reference each other). Do not add it to every module by default.
- **Configured classes** must be `@pconfiged` and have:
  - `config: <ConfigType>` (the attribute name is always exactly `config`)
  - `def __init__(self):` is optional if it would be empty; if defined, it must take no arguments.
  - Runtime objects are constructed via `<ConfigType>(...).construct()`, not via passing kwargs into `__init__`.
- **Config types** must be separate classes decorated with `@pconfig(...)`:
  - Use `@pconfig(constructs=TheClass)` for classes you own / can modify.
  - Keep config classes minimal: type hints only; no side effects at import time.
- **Defaults** must be defined separately using `pdefaults += ...` (avoid cluttering the type definition).
- When you want the default value of a config type, use `pdefaults(MyConfig)` rather than `MyConfig()`. This reads clearly as "use the defaults" and applies everywhere: config instance files, `pdefaults +=` blocks, and module code.
- Do not cache config values on `self`; always read them from `self.config`:
  ```python
  # WRONG — caches config value as instance attribute
  def __init__(self):
      self.learning_rate = self.config.learning_rate

  # CORRECT — reads from self.config at point of use
  def train_step(self):
      optimizer.param_groups[0]["lr"] = self.config.learning_rate
  ```
- Do not duplicate values already present in sub-configs; always read them from the sub-config.
- Do not define `__init__` methods when they contain no logic.
- Construct sub-config objects once in `__init__` and reuse them in methods:
  ```python
  # WRONG — constructs on every call
  def train_step(self):
      reader = self.config.reader_config.construct()
      reader.read()

  # CORRECT
  def __init__(self):
      self.reader = self.config.reader_config.construct()
  ```
- When a derived `@pconfiged` class specializes a constructable sub-config (e.g., `plotter_config: CustomPlotterConfig` instead of the base `PlotterConfig`), add a type-narrowing reassignment:
  ```python
  self.plotter: CustomPlotter = self.plotter
  ```
  Place this in the same method where the base class calls `.construct()` on the sub-config.
- When a module defines multiple pconfiged objects with configs and defaults, order each trio as: Class, Config, pdefaults, then repeat.
- For pconfiged classes, any optional method behavior should be expressed via config fields when the values are simple types (or simple containers of those types) or other config types.
- Minimize use of the `Required` sentinel; reserve it for mandatory full paths (S3 or disk), not for relative paths.
- When defining ranges, prefer a single tuple field over separate start/end parameters.
- When configuring external functions/classes, use pconfigs external interfaces with sub-configs instead of placing those parameters directly on the parent config.
- Config fields must be simple scalar types (str, int, float, bool), `Type[...]` references, or sub-configs; never use `Callable` or other complex types.
- Never add config fields that are not used by the class the config constructs. If a field is needed by a base class, inherit from the base class's config type rather than duplicating the field.
- When a derived `@pconfiged` class has its own environment config, that environment must inherit from the base class's environment config to preserve inherited fields.

### Subconfigs (composition over registries)

- Prefer hierarchical configs: `SystemConfig` holds `trainer_config: TrainerConfig`, etc.
- Never implement string registries or `if/elif` factories to pick submodule types. Let configs carry the constructable type.
- Never implement dispatch functions that inspect a config's type (via strings, dicts, `isinstance`, or any other mechanism) to decide which object to construct. Each config type must construct its own object via `@pconfig(constructs=...)` and `.construct()`. If you find yourself writing a function that takes a base config type and returns different objects depending on which derived config was passed, that function is a factory — replace it with pconfiged polymorphism. (This rule does not apply to `@pproperty` methods that use `isinstance` on sibling sub-configs to compute derived values or pin fields — that is config-time wiring, not runtime dispatch.)

### Directory separation (non-negotiable)

Directories containing a `__pconfigs__.py` sentinel are config-instance-only directories. They must contain only:
- Config instance files (files that define `config = ...` instances)
- `__init__.py` for package structure
- `__pconfigs__.py` sentinel (must be empty or contain only ptest sentinels `TestSubdirs` or `TestManually`)
- Subdirectories following the same constraint

Never place module code (`@pconfiged` classes, `@pconfig` types, or `pdefaults` definitions) in a directory containing a `__pconfigs__.py` sentinel. Module code belongs in `modules/` or other type-definition directories.

### Computed config fields (pproperties) — basics

- Use `@pproperty` for computed fields that are evaluated at config construction time.
- Every `@pproperty` must have a corresponding type-annotated class field.
- If a `@pproperty` does not use `pinputs(...)`, its class field must be typed as `Pinned[T]`.
- When a property needs the user-provided input, read it via `pinputs(self)` (do not read back `self.<field>` when you need the original user value).
- Every `Pinned[T]` field must have a corresponding entry in `pdefaults` set to the `Pinned` sentinel (not a concrete value):
  ```python
  pdefaults += MyConfig(
      derived_field=Pinned,
  )
  ```
  The `Pinned` sentinel tells pconfigs that this field is managed by a `@pproperty` and must not be set by users.
- `pinputs(self)` vs `self`: Inside a `@pproperty` for field X, `self.X` returns the pproperty-computed value (i.e., the return value of this pproperty), while `pinputs(self).X` returns the raw user-provided value. The primary use of `pinputs(self)` is to read the user-provided value of the field the current pproperty is overwriting — e.g., a pproperty for `optimizer_config` reads `pinputs(self).optimizer_config` to copy and modify the user's input. Other pproperties that need `optimizer_config` should read `self.optimizer_config` to get the final computed version.
- When configs include multiple `Pinned` fields, list user-settable fields first and group `Pinned` fields at the end.
- If a field is computed/overwritten and users must not set it, type it as `Pinned[T]` and set it with `Pin(value)` in code.
- `Pin(...)` is only used when constructing configs (e.g., `ConfigType(x=Pin(...))`); `@pproperty` methods should return plain values.
- Do not mark every field in a sub-config as `Pinned[...]`. If a sub-config is fully derived, keep its fields simple and pin the parent field that holds the sub-config.
- (non-negotiable) Never use `Pin` in user config files; it is for module code that defines system wiring.
- Use `psetter(...)` only when you must set deeply nested fields and the explicit constructor nesting becomes unreadable.
- For detailed pproperty patterns (derived types, guard clauses, sub-config construction), see the pproperty rules file.

### Config instance files (experiment configs)

- Only define config instances (typically a single `config = ...`).
- Prefer copying a base config by passing it as the first positional argument:
  ```python
  from other_pconfig import config as base
  config = SomeConfig(
      base,
      parameter="value",
  )
  ```
- When overriding a sub-config field, always pass the base's sub-config as the first argument to preserve inherited values:
  ```python
  # WRONG: loses all other fields from base
  config = SomeConfig(
      base,
      sub_config=SubConfig(
          another_parameter="new_value",
      )
  )

  # CORRECT: inherits all fields from base, overrides only specified field
  config = SomeConfig(
      base,
      sub_config=SubConfig(
          base.sub_config,
          another_parameter="new_value",
      )
  )
  ```
- Do not use `Required` in instance files; use concrete values for required fields.
- Do not set `Pinned[...]` fields in instance files; pinned values are wired in module code.
- Do not use `pdefaults(TypeName)` inside a config construction block; defaults are already copied:
  ```python
  # WRONG
  profiler_config = PyTorchProfilerConfig(
      pdefaults(PyTorchProfilerConfig),
      filename=None,
  )

  # CORRECT
  profiler_config = PyTorchProfilerConfig(
      filename=None,
  )
  ```
- When creating the first config instance for a new config type, include the salient conceptual parameters explicitly and set them to their default values so the important options are visible. Avoid internal implementation details (paths, key strings, filenames); only include user-relevant parameters.

### Environments

- Environment config types use `@penv(convention="uppercase")`.
- The environment field in configs is always named exactly `environment`.
- Prefer env defaults by subclassing the env type and adding default values on fields.
- Always use environment configs for machine-specific values (paths, system resources, debug flags); treat this as a strict requirement and keep env usage limited to those cases.
- Never use `pdefaults` with `@penv`; set defaults directly on the env class fields.
- Never use empty-string sentinels for env vars; use `None` to represent "unset."
- Env vars must use simple types only (e.g., `str`, `int`, `float`, `bool`); avoid unions like `str | None`. You may still use `None` as a default value.
- Do not include `environment` in `pdefaults` for configs.
- Define environment config classes immediately above the config class that uses them. When a pconfiged class's config uses an environment, the env class goes between the pconfiged class and its config class (satisfying both the trio ordering and the "immediately above" placement):
  ```python
  @pconfiged
  class System:
      config: SystemConfig

  @penv(convention="uppercase")
  class SystemEnv:
      data_dir: str = None

  @pconfig(constructs=System)
  class SystemConfig:
      environment: SystemEnv
  ```

### Enums

- Use `@penum` for enum-like config values so printing is interpretable.
- Do not subclass/extend enums (Python forbids adding members in subclasses). If you need more values, define a new `@penum` type.
- When creating enums or using @penum, use string literals that convert from CapitalCase to snake_case.

### External libraries — basics

- If an external class has simple optional kwargs, configure it with `@pconfig(mocks=ExternalClass)`.
- If an external function has defaults, configure it with `@pconfig(calls=func)`; name the config type with a `Func` suffix and no `Config` suffix.
- Config classes created with `@pconfig(calls=...)` are callable and should be invoked directly; do not use `.construct()` on them.
- Never use string/dotpath registries or dynamic imports to instantiate external classes or call external functions.
- For detailed external library wrapping rules (mocks, calls, wrappers, signature handling), see the external library rules file.
- Use `Omitted[T]` for external parameters whose type is complex (no simply-typed member). For parameters with a simple type or a narrowable simple member, declare them as regular config fields with explicit defaults in `pdefaults`. If you want to pass a runtime value for an omitted parameter via `.construct(..., param=runtime_value)`, ensure the config's value is set to the `Omitted` sentinel in `pdefaults` (or in the config instance).

```python
# Example usage of @pconfig(mocks=...) and @pconfig(calls=...)
@pconfig(mocks=SomeClass)
class SomeClassConfig:
    pass

some_class = some_class_config.construct(param_without_default="some value")

@pconfig(calls=some_function)
class SomeFunc:
    pass

some_result = SomeFunc(param_without_default="some value")
```

### Running / entrypoints

- For runnable systems use `@pconfiged(runnable=True)` and implement `def main(self, *args, **kwargs):`.
- Avoid adding argparse flags; in pconfigs systems, CLI args are considered an anti-pattern. Prefer fully-specified runnable configs.
- Run pconfigs config files using `python -m pconfigs.run dotpath.to.module.config` where the final `.config` refers to the name of the config object in the module `dotpath.to.module`.
- Runnable `main` methods must use one of these signatures:
  1. `def main(self, *args, **kwargs)`
  2. `def main(self, parsed_args: Namespace, other_args: List[str])`
- When using `@pconfiged(runnable=True)`, the class inherits from `ConfigRunnable`. To access the config dotpath string (e.g., for logging or initializing a run directory), you must use signature (2) above and access `parsed_args.config`.
- Runnable `main` methods must return `int` (follow `config_runner.py`).

### How to inspect a pconfigs config (non-negotiable)

The printed config is the source of truth for **everything** about a pconfigs run, including (a) which entrypoint executes, (b) which classes get constructed, (c) which subclass replaces a base class, (d) the full sub-config tree, and (e) every field value. Source files cannot answer these questions: pconfigs computes the answer at construction time by merging defaults, evaluating `@pproperty` methods, and resolving inheritance chains. Reading source to infer runtime behavior is a habit transferred from non-pconfigs codebases and will produce wrong answers here.

**Before grepping or reading any source file to answer a question about an experiment, config, or run**, print the relevant config to a file and grep that file. The following are violations of this rule:

- Grepping the source for `class FooConfig` to find out what fields a config has.
- Reading a `.py` file to determine which subclass of a base class will be constructed at runtime.
- Tracing imports to figure out the entrypoint of a runnable config.
- Reading `pdefaults += ...` blocks to determine the effective default of a field.
- Inferring TB tag strings, log paths, or any other resolved value from `@pproperty` methods in source.

The fix in every case is the same: print the config, grep the printed file.

**Print once and reuse.** A printed config is good for the whole session unless the part of the config you're asking about has changed in source. Cache the file at `/tmp/pconfig_<dotpath_tail>.py` and reuse it across questions; do not reprint between questions.

```bash
# 1. Check whether a relevant printed config is already cached.
ls /tmp/pconfig_*.py 2>/dev/null

# 2. If not cached, print once.
python -m pconfigs.print <dotpath>.config > /tmp/pconfig_<dotpath_tail>.py

# 3. Grep the printed file for whatever you need.
grep -n "<thing>" /tmp/pconfig_<dotpath_tail>.py
```

**Reprint only when:**

- The config dotpath changed (you're asking about a different experiment).
- The part of the config tree you're asking about has been edited in source since the cache was written.
- You need 100% confidence the implementation matches the latest code (e.g., before committing, before launching a run, when verifying a specific edit landed).

For "I want to understand what this experiment does" or "I'm planning a change," the cached print is sufficient. Re-reading source to update an in-memory model of the config is the wrong move — keep using the printed file.

**Cite the printed-config path in any answer that names a runtime value, class, entrypoint, or sub-config wiring** (e.g., `/tmp/pconfig_encoded_latents_loss.py:15163`). If your answer doesn't cite a printed-config line, you didn't consult the source of truth.

**Mental model:** Think of `.py` source as the pre-construction template and the printed config as the post-construction reality. Pconfigs is a compilation step from template to reality. Your reasoning must be against the post-construction reality, not the template.

The printed output can be extremely large (over 10,000 lines). Never read the entire output — always grep it for the specific field, class, or sub-config you need.

### Printing & testing

- Ensure configs remain printable with `repr(config)` (import paths + values).
- Keep import-time side effects (logging/warnings) minimal so `python -m pconfigs.print ... > file.py` yields clean output.
- Test individual pconfigs files by running `python -m dotpath.to.module`.
- Test all pconfigs in the repository by running `ptest`.
- Use `TestSubdirs` / `TestManually` sentinels in `__pconfigs__.py` when needed.


### Typing rules (Python 3.10)

- Never use quoted/string literal annotations; rely on `from __future__ import annotations` instead.
- If you create a "type alias" used in annotations, declare it with `TypeAlias`:
  - `from typing import TypeAlias`
  - `MyAlias: TypeAlias = ...`
- Prefer explicit return types for public methods and `@pproperty` functions.
- When returning more than two values from a method, use a dataclass with named fields instead of a tuple.
- Avoid type hints with more than 2 levels of nesting (e.g., `Optional[Tuple[Optional[float], Optional[float]]]` has 3 levels). When nesting exceeds 2 levels, extract a well-named `TypeAlias` and place it directly above its first use.

### When to use derived classes vs sub-configs vs config switches

**Config switch (simplest)** — Use when:
- The variation is a simple on/off or a choice among a small fixed set with no additional parameters.
- The new code path is short and lives inside an existing method, guarded by the switch.

**Sub-config with helper object (middle ground)** — Use when:
- The new behavior can be encapsulated in a separate object that the existing class calls into.
- The existing class delegates to a config-specified helper rather than adding conditional branches.
- Users who do not want the new behavior omit the sub-config (set it to `None`) or specify an identity implementation of the helper that passes data through unchanged.
- The new code lives in the helper object, not in the existing class.

**Derived class** — Use only when there is a large structural change: new methods, different control flow, different state management that cannot be delegated to a helper.

**Evolution path**: Start with a config switch. If the variation grows into a cohesive concept with its own parameters, refactor into a sub-config with a helper object. Only create a derived class when the structural differences cannot be delegated.

**Anti-pattern**: Creating a derived class for a small computational variation (e.g., `ClampedModule` for clamping a tensor). This leads to class explosion.

### Future-proof design

Refactoring can never break existing experiments (hard repo policy). When adding a new config field, follow these steps to choose the right abstraction level and placement:

1. What concept does this variation belong to?
   - Data transformations on raw inputs → dataset config.
   - Transformations on internal representations (latents, embeddings) → module config.
   - How loss interprets target values (weighting, reduction) → loss/module config.
   - If unclear, ask: which component is responsible for ensuring this value's consistency?
2. Name the field for what it IS, not how it will be used.
   - Example: `target_range` (the concept), not `target_clamp_range` (the operation). The concept-level name allows the type to evolve (e.g., from `Optional[Tuple[float, float]]` to a `TargetRangeConfig`) without renaming.
3. Is the field the right level of generality?
   - Imagine two or three plausible future extensions of this concept.
   - Would each extension require a new top-level field on the parent config? If yes → the abstraction is too specific. Group related concerns into a single sub-config whose internal structure can evolve independently.
   - Would each extension fit as a new field on a sub-config? If yes → the abstraction level is correct.
4. Choose the lightest-weight implementation (see "When to use derived classes vs sub-configs vs config switches").
   - Design for additive evolution: new config fields with defaults, new sub-configs that subsume existing fields.

### Codebase evolution

- If a correctly named config field would require introducing a more general type that is not otherwise needed, keep the field name correct and allow a more specific typehint for now. Introduce the more general type only when there is a concrete need for multiple implementations.

### Modules and files

- A module should define one primary concept (plus helper types) and the module filename should match that primary concept.
- Module filenames should generally use 2–3 underscores at most.

### Helper files and directories

- When a module `my_thing.py` needs auxiliary files (shell scripts, templates, data files, etc.) that contribute to the module's concept without defining a new entity, use the `_helpers` suffix:
  - If a single helper file suffices: create `my_thing_helpers.py` alongside `my_thing.py`.
  - If multiple helper files or non-Python files are needed: create a `my_thing_helpers/` directory alongside `my_thing.py`.
- Helper directories are not Python packages; do not add `__init__.py` unless the helpers are importable Python modules.
- When referencing helper files from Python code, construct paths relative to the module using `os.path.dirname(__file__)`.

### Pconfig instance files

- Pconfig instance files may encode concepts that are more specific than the typenames they instantiate. When naming a pconfig instance file, ask:
  1. What concept is implemented by this instance?
  2. Is it more specific than the typenames used?
  3. If so, choose a shorthand filename that reflects the more specific concept and stays within the 2–3 underscore limit.

### File operations (non-negotiable)

- When moving or renaming files, use terminal commands (`mv`, `cp`) instead of reading and rewriting file contents.
- Rewriting files risks introducing transcription errors; moving preserves content exactly and maintains git history.
- Only use the write tool for files that require actual content changes, not for relocations.
- When restructuring directories, clean up empty directories (including `__pycache__/`) with `rm -rf`.
