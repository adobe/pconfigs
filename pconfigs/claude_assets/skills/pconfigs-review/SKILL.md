---
name: pconfigs-review
description: "Self-review checklist for pconfigs code. Use after writing any pconfigs code — configs, pconfiged classes, pproperties, or experiment instance files — to catch common mistakes before submitting."
---

# pconfigs Self-Review

After writing pconfigs code, walk through each checklist item below. For every
item that applies to your code, verify it is satisfied. Fix violations before
presenting your answer.

## 1. External vs internal code

When wrapping code you do not own (external libraries, third-party classes or
functions):

- [ ] External **classes** use `@pconfig(mocks=ExternalClass)` with a `Config`
  suffix. Constructed via `.construct()`.
- [ ] External **functions** use `@pconfig(calls=external_func)` with a `Func`
  suffix (no `Config`). Invoked directly as a callable.
- [ ] You did NOT use `@pconfig(constructs=...)` or create a custom
  `@pconfiged` wrapper for an external type. `constructs=` is only for classes
  you own and control.

## 2. Method parameters on @pconfiged classes

- [ ] Methods on `@pconfiged` classes do NOT accept parameters that select
  between behaviors (e.g., a "mode" or "strategy" string). Such choices belong
  on the config as `@penum` fields, read via `self.config` at point of use.
- [ ] No method has default parameter values (`= ...`).
- [ ] No method uses `*args` or `**kwargs`.

## 3. @pproperty patterns

When a `@pproperty` overwrites a user-provided sub-config field:

- [ ] The user-provided value is read via `pinputs(self).field_name`, not
  `self.field_name`.
- [ ] Derived config types are preserved using the `type(inputs)` pattern
  (`InputConfig: Type[T] = type(inputs)`), not by hardcoding the base type.
- [ ] Pinned values use `Pin(...)`.
- [ ] Fields that have no `@pproperty` are read via `self`, not `pinputs(self)`.

When a `@pproperty` computes a value without reading the user-provided value
of its own field:

- [ ] The field is typed `Pinned[T]`.
- [ ] `pdefaults` sets the field to the `Pinned` sentinel.

## 4. Enum and mode patterns

- [ ] All if/elif chains that check config options use `@penum` types, not raw
  strings.
- [ ] Comparisons use `is`, not `==`.
- [ ] Every if/elif chain ends with `else: raise ValueError(...)`.
- [ ] Blank line between `if` and `elif` blocks; no blank line before a short
  `else`.

## 5. Config construction and naming

- [ ] Attributes constructed from `self.config.<name>_config` are assigned to
  `self.<name>` (drop the `_config` suffix).
- [ ] Sub-configs are constructed once in `__init__` and reused, never
  reconstructed per method call.
- [ ] Config values are read from `self.config` at point of use, never cached
  on `self`.

## 6. Config instance files

- [ ] `base` is passed as the first positional argument when deriving from
  another config.
- [ ] When overriding a sub-config, `base.sub_config` is passed as the first
  positional argument to the inner constructor to preserve inherited fields.
- [ ] No use of `pdefaults(...)` inside config construction blocks.
- [ ] No `Pinned` fields are set in instance files.

## 7. Modification safety

- [ ] Before modifying existing code, you determined whether experiments have
  produced valid results.
- [ ] Small variations are implemented via config switches with
  backwards-compatible defaults, not via derived classes.
- [ ] No existing runnable pconfig instance would behave differently after your
  change.
