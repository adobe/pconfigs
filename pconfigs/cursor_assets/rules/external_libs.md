---
description: "Rules for wrapping external library classes and functions with pconfigs (@pconfig mocks and calls), including signature handling, wrapper functions, and placement conventions"
globs: ["**/*.py"]
---

## External library wrapping rules

### Placement of project-general external configs

When creating configs that mock or call external library code with no module-specific customizations, place them at the project's import root in a directory called `external_configs`. Organize files within `external_configs` using subdirectories that mirror the external library's import path (e.g., `external_configs/torchmetrics/image.py` for `torchmetrics.image.StructuralSimilarityIndexMeasure`). Only project-general customizations (e.g., changing a default that makes sense project-wide) are allowed in this directory. Module-specific specializations must live in the module that uses them.

### Choosing the right wrapper

Follow these steps in order when wrapping an external library class or function:

1. Is it a function or a class?
   - Function → go to step 2.
   - Class → go to step 3.
2. (Function) Does the function have optional kwargs with defaults?
   - No optional kwargs → no config is needed; call the function directly.
   - Yes, but some defaults are not simple types → write a wrapper function with simple-typed params that constructs complex kwargs internally, then use `@pconfig(calls=wrapper_func)`.
   - Yes, and all defaults are simple types → use `@pconfig(calls=the_function)` directly. Name the config type with a `Func` suffix and no `Config` suffix.
3. (Class) Are all constructor args simply typed (str, int, float, bool, or sub-configs)?
   - Yes → use `@pconfig(mocks=ExternalClass)` so defaults are auto-read.
   - No, but you only need a few simple fields → wrap it in a small derived `@pconfiged(mock=True)` class whose config contains only simple fields.
   - No, and the constructor is huge/complex → wrap it in a small derived `@pconfiged(mock=True)` class whose config contains only simple fields, and pass complex args at `.construct()` time.

### @pconfig(calls=...) rules

- Config classes created with `@pconfig(calls=...)` are callable and should be invoked directly (e.g., `result = some_func_config()`).
- Do not use `.construct()` on `@pconfig(calls=...)` configs.
- When an external API expects a callable (e.g., a schedule function), you can pass the config object itself (e.g., `schedule=some_func_config`) rather than invoking it.
- Do not annotate parameters that already have defaults in the external function; pconfigs will infer those from the signature.
- Read the function signature. Any parameters without defaults must be either annotated on the config class (with defaults added) or provided at call time.

### @pconfig(mocks=...) rules

- Do not define an `__init__` method. Declare the config class separately and include the mocked signature's parameters verbatim as config fields.
- Only add config fields when the external `__init__` lacks defaults or when you need a more specific typehint. To override just the default value of an externally-read field without changing or specializing its type, set the new default in `pdefaults +=` rather than re-declaring the field in the config class body. The decorator auto-reads all fields from the external signature, so the class body should contain only fields whose types differ from the external signature.

### Reading external signatures

When creating configs for external interfaces, find the source file in the active Python environment and read the function/class signature from that source file. Handle these cases:
1. No defaults and no typehints: infer types from code and add annotations with defaults when possible. If a required type is not simple, do not expose it as a config field. Use a wrapper with simple inputs or pass the value at `.construct(...)` time.
2. No defaults but typehints: add annotations and defaults if simple; otherwise omit the field and require callers to pass the value at `.construct(...)` time.
3. Defaults without typehints: infer the type from the default; if the default is `None`, read the code to infer the type and apply case 1/2 rules.
4. Defaults with complex typehints (or `None` defaults for complex types): do not expose complex-typed fields as config fields. Pass them at `.construct(...)` time or wrap with a simple-typed interface.

### Omitted usage (non-negotiable)

- If an external parameter's type is complex (no simply-typed member in its annotation), use `Omitted[T]` regardless of whether you pass a value at runtime. Complex-typed parameters are outside the config's domain.
- If code needs to pass an omitted value at runtime via `.construct(..., param=runtime_value)`, you must set the config's value to the `Omitted` sentinel in `pdefaults` (or in the config instance). The `Omitted[T]` annotation alone is not enough.
  - Example: `pdefaults += MyMockedConfig(param=Omitted)` so `MyMockedConfig(...).construct(param=runtime_value)` is allowed.
- If an external parameter's type has a simply-typed member (e.g., `Union[str, Strategy]` has `str`) and you want to configure it, narrow the annotation to the simple type and declare it as a regular config field with an explicit default in `pdefaults`.
- Do not use `Omitted[T]` for parameters that have a simple type or a narrowable simple member — declare them as regular config fields with explicit defaults instead of silently inheriting the external default.
- When a parameter defaults to `None` and has no type hint, look up the intended type. If it is simple, declare as `Optional[<simple_type>]` with `None` default. If it is complex, use `Omitted[T]`.

### Additional rules

- Do not create pconfig fields for `None`-defaulted parameters that require complex types. If a union includes a simple type that is sufficient for the current use case (e.g., `Optional[Union[str, Path]] = None`), you may treat it as simply typed and use that simple type for config defaults.
- For external function configs, any config fields not in the external function signature must be typed as `NotMock[T]`.
- If an external function lacks type hints and has required parameters, those parameters cannot be configured directly; either pass them at call time or wrap the function to add type hints and defaults.
- For external function/class configs, only add annotations when changing the external type; if the external function lacks type hints, include all optional parameters as annotated config fields.
- Special cases for wrapper functions:
  1. The external function has no optional kwargs (then no config is needed).
  2. The external function has optional kwargs whose defaults are not simple types; in that case, define a wrapper with simple-typed params and construct complex kwargs internally.
