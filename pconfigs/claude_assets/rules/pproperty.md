---
description: "Detailed @pproperty patterns for computed config fields, including derived type preservation, guard clauses, pinputs usage, and cross-cutting properties"
globs: ["**/*.py"]
---

## pproperty patterns

### Pattern selection checklist

When writing a `@pproperty`, follow these steps in order to determine which pattern to use:

1. Does the pproperty use `pinputs(...)`?
   - No → the class field must be typed as `Pinned[T]`. You may construct the return value however you need.
   - Yes → continue to step 2.
2. Does the pproperty return a pconfig object?
   - No → return the computed value directly; no special pattern is needed.
   - Yes → continue to step 3.
3. Must derived config types be preserved? (i.e., could a derived experiment pass a subclass of the declared return type that must survive the pproperty?)
   - No → use the **simple pattern** (hardcode the base config type).
   - Yes → continue to step 4.
4. Must the pproperty adapt its behavior per derived type? (e.g., pin a field that only exists on a subclass)
   - No → use the **inputs/InputConfig pattern** (preserves the derived type without branching).
   - Yes → use the **guard clause pattern** (isinstance checks with an else that raises TypeError).

### Basic patterns

When a `@pproperty` returns a pconfig object, you may construct it however you need in that method; if you do not use `pinputs(...)`, the field annotation must be `Pinned[T]`.

**When derived configs are not needed** (step 3 = No) — use the simple pattern:
```python
@pproperty
def my_thing_config(self) -> MyThingConfig:
    config = MyThingConfig(pinputs(self).my_thing_config, some_property=Pin(...))

    return config
```

**When derived config types must be preserved** (step 3 = Yes, step 4 = No) — use the `inputs`/`InputConfig` pattern:
```python
@pproperty
def my_thing_config(self) -> MyThingConfig:
    inputs = pinputs(self).my_thing_config
    InputConfig: Type[MyThingConfig] = type(inputs)
    config = InputConfig(inputs, some_property=Pin(...))

    return config
```

Always colocate the `inputs` and `InputConfig` lines at the top of the `@pproperty` body. The `InputConfig` type annotation must use `Type[T]` where `T` is the return typehint of the `@pproperty`.

### When to use each pattern

- Use the `inputs`/`InputConfig` pattern only for configs whose return type is the `@pproperty`'s declared return type — i.e., the config that the property is responsible for returning.
- For sub-configs constructed within the property body (e.g., helper configs passed as kwargs), use the hardcoded base type directly.
- Adopt the derived-type-preserving pattern for a sub-config only when a concrete need arises (e.g., a derived experiment actually passes a derived sub-config type that must be preserved).

### Guard clauses for derived config types (step 4 = Yes)

When a `@pproperty` must adapt its behavior for derived config types (e.g., pin a field that only exists on a subclass), check the input config's type explicitly with `isinstance` — never use `hasattr` or duck-typing. Include an `else` clause that raises `TypeError` for unhandled config types:

```python
@pproperty
def my_thing_config(self) -> MyThingConfig:
    inputs = pinputs(self).my_thing_config

    if isinstance(inputs, MyThingConfig) and not isinstance(inputs, DerivedMyThingConfig):
        return inputs

    elif isinstance(inputs, DerivedMyThingConfig):
        InputConfig: Type[DerivedMyThingConfig] = type(inputs)
        config = InputConfig(inputs, extra_field=Pin(...))

        return config
    else:
        raise TypeError(f"Unhandled config type: {type(inputs)}")
```

When a `@pproperty` only needs to pin fields on specific derived config types, use a guard clause that returns the input unchanged for the base type, then use `type(inputs)` to preserve the derived type when constructing the pinned version.

### Sub-config construction within pproperties

- When constructing a sub-config to pass as a kwarg in a larger config construction, always copy from the input's corresponding sub-config as the first positional argument:
  ```python
  # WRONG — silently discards user overrides on sub_config
  config = ParentConfig(inputs, child_config=ChildConfig(pinned_field=Pin(...)))

  # CORRECT — preserves user overrides
  config = ParentConfig(inputs, child_config=ChildConfig(inputs.child_config, pinned_field=Pin(...)))
  ```
- Use the type that matches the declared type on the parent config — not a simpler base type. If the parent config declares `sub_config: DerivedSubConfig`, construct `DerivedSubConfig`, not `BaseSubConfig`.
- When pconfigs raises a "parent initialized from child" error, this signals a type mismatch: fix the constructed type to match the input's type, rather than working around the error by forwarding individual fields.

### Immutability

Never mutate input configs returned by `pinputs(self)`; always create a new config by copying from the input config.

### If derived configs are not needed but a pproperty must adapt for derived types

Use a guard clause that returns the input unchanged for the base type, then construct the pinned version using `type(inputs)`:
```python
@pproperty
def dataset_config(self) -> DatasetConfig:
    inputs = pinputs(self).dataset_config

    if type(inputs) is DatasetConfig:
        return inputs

    InputConfig: Type[DatasetConfig] = type(inputs)
    config = InputConfig(inputs, some_field=Pin(...))

    return config
```

## Cross-cutting properties

- A value X is a conceptual property of config M if M is responsible for ensuring X's consistency across the sub-components M wires together (e.g., a system config ensuring that a module's output mode matches the datasets' output mode).
- Express a conceptual property as a `@pproperty` when it has two or more consumers among M's other pproperties. A single consumer does not justify the indirection.
- When a cross-cutting value originates from a sub-config (e.g., `module_config.model_config.out_mode`) and must be pinned into other sub-configs (e.g., dataset configs), the pproperty should read the value from `pinputs(self).module_config.model_config` rather than `self.module_config.model_config` to avoid creating dependency cycles. Extracting the value into its own pproperty makes this safe-by-construction: downstream pproperties read `self.out_mode` (which depends only on user inputs), not `self.module_config` (which is a computed pproperty that may itself depend on the downstream pproperties).
