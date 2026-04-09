---
description: "Naming conventions for classes, configs, variables, functions, properties, and config fields"
---

## Naming conventions (non-negotiable)

### Class and config naming

- Name all @pconfiged classes in the style of `MyClass` (upper camel case).
- Name all @pconfig classes in the style of `MyClassConfig` (matching the @pconfiged class with suffix `Config`), except for external function configs which should be named `MyFunc` (no `Config` suffix).
- Refer to derived classes of MyThing as "DerivedMyThing", up to 40 characters (where "Derived" is whatever special name makes sense).
  - Example lineage: Model, SpecialModel(Model), ExtraSpecialModel(SpecialModel), ReallyExtraSpecialModel(ExtraSpecialModel)
  - When the new name would exceed 40 characters, judiciously use acronyms to decrease name lengths while keeping it human readable. Retain some of the ending words so the reader knows what the base of the class lineage is. For example: `MuchMoreEMFRESpecialModel(EvenMoreFoshoReallyExtraSpecialModel)`
  - When adding more acronyms would make the name unreadable, create nicknames. Retain some of the ending terms so the reader knows what the base class lineage is:
    ```python
    class EvenMoreMMEMFRESpecialModel(MuchMoreEMFRESpecialModel):  # BAD
    class CustomSpecialModel(MuchMoreEMFRESpecialModel):           # GOOD
    ```
- Preserve acronym capitalization in class, function, and variable names (e.g., `MNISTDatasetConfig`, not `MnistDatasetConfig`).

### Class naming checklist

Apply these steps in order before proposing a name:
1. What does the class DO or what IS it? (not: what is it used for)
2. Does it derive from a base class? If so, the suffix must match the base class name (`DerivedMyThing` pattern).
3. What single word or short phrase captures the essential difference from the base? That becomes the prefix.
4. Is any substring redundant with another substring or with the base class name? If so, remove it.
5. Does the name sound like a verb? If so, find a noun that describes the same concept.
6. Apply the name scoping rule: can any part be dropped because the containing namespace already provides that context?

Do NOT reason by association with the feature's intended use or surrounding context. Apply the checklist mechanically.

### Variable naming checklist

Apply these steps in order when naming any variable, parameter, or attribute. Do not skip steps or jump to an intuitive answer.
1. **Identify the scope**: Is this a class attribute, function/method parameter, or local variable?
2. **Start from the type**: If the type is a custom class, the default name matches the type (e.g., `SubsetDataset` -> `subset_dataset`). If the type is a basic type, choose a descriptive name.
3. **Apply scoping drops**: Can any part of the name be omitted because the containing namespace (class, function, module, directory) already provides that context?
4. **Check config-field correspondence** (class attributes only): If this attribute is constructed from `self.config.<name>_config`, the attribute must be named `<name>`.
5. **Check ambiguity** (class attributes only): Is the type-derived name ambiguous in this class? If so, apply the instance disambiguation rule.
6. **Verify no rule conflicts**: Re-read the proposed name against the other naming rules (redundancy, synonyms, literalness, general-left/specific-right).

Function parameters and local variables do NOT get class-level disambiguation qualifiers — their scope is the function, and the function name provides context.

### Core principles

- Variable names must be literal, precise, and consistent. If you choose a base term `<name>`, use it consistently and pluralize it when the value is a collection:
  ```python
  # WRONG
  for s in sample_list:

  # CORRECT
  for sample in samples:
  ```

- Never introduce synonyms for the same concept. If something is called `THING`, always call it `THING` everywhere:
  ```python
  # WRONG: introduces synonyms "img", "picture", "photo" for the same concept
  def process_image(img: Tensor) -> Tensor:
      picture = normalize(img)
      photo = resize(picture)
      return photo

  # CORRECT: consistent use of "image" throughout
  def process_image(image: Tensor) -> Tensor:
      image = normalize(image)
      image = resize(image)
      return image
  ```

- Names must describe what the thing does (no more, no less); do not name by intended use.

- Names must be objective descriptions, not subjective judgments. For example, `QuietProfiler` is incorrect because "quiet" is a judgment about the output's nature; the correct name describes what the profiler does: `NoSummaryProfiler` (suppresses summary output).

- Never use a verb or participle alone as a name without its object/subject. Names must be grammatically complete:
  ```python
  clamped          # BAD — clamped what?
  clamped_targets  # GOOD — targets are clamped
  ```

- Avoid redundant substrings within a name. Each substring should carry meaning not already captured by other substrings or by the containing context. For example, in a training system, "Module" already implies "the thing being trained," so "TrainingModule" is redundant — use "Module" instead.

### Type-name rule

- For variables whose type annotation is a custom class (e.g., `LinspaceFunc`, `HatDatasetWriterConfig`), name the variable to match its type (e.g., `linspace_func`, `hat_dataset_writer_config`).
- Do not apply the type-name rule to basic types (`int`, `float`, `str`, `bool`, `Tensor`, containers of these):
  ```python
  # WRONG: naming basic types after their type
  def process(tensor: Tensor, int: int) -> Tensor:

  # CORRECT: descriptive names for basic types
  def process(image: Tensor, scale: int) -> Tensor:
  ```
- When constructing an object from `self.config.<name>_config`, assign it to an attribute named `<name>`:
  ```python
  # WRONG
  self.data_reader = self.config.reader_config.construct()

  # CORRECT
  self.reader = self.config.reader_config.construct()
  ```

### Naming discrepancy check

When applying the naming rules produces a variable/field name that does not match the snake_case conversion of its type name (after allowed scoping drops), treat the mismatch as a signal that the type name may be incorrect. Before accepting the discrepancy, verify that the type name accurately describes the veridical nature of the thing it models. If the type name contains a qualifier (e.g., a project-specific prefix) that forced the field name to diverge, the qualifier is likely wrong. Correct the type name first, then re-derive the field name.

### Scoping and context

- You may drop a shared prefix from a variable name when the containing scope already provides that context (e.g., `HatDatasetReaderConfig` containing a `HatDatasetWriterConfig` may use `writer_config`).
- Name scoping rule: if a suffix or prefix `<concept>` matches a similar string in the containing namespace (directory name, config/class/function name), you may omit `<concept>` from the local name because the context already provides it.
- When assigning the result of a function call, name the variable to reflect the function name unless the function name is nonsensical; you may drop redundant prefixes if context is clear:
  ```python
  decoded_latents = self.decode_latents(...)       # reflects function name
  target_size = self.dataset_config.get_target_size()  # drops get_ prefix
  ```

### General-left / specific-right ordering

- When naming variables, put the more general category on the left and the specialization on the right (e.g., `key_x`, `key_y`), except when there is only a single item of that category in the codebase (e.g., `data_dir`, `sample_path`).
- When there are multiple valid groupings, choose the one that aligns with how users will conceptually cluster the parameters. Consistency with the surrounding naming scheme takes precedence over a mechanical category/specialization decomposition.

### Config field naming

- When naming config fields, consider: the config class meaning, each field's purpose, and whether each field name/type is as general as possible without losing clarity.
- If a config field is more specific than the config class name implies, rename the field and its type to the most general name that matches the config class meaning:
  ```python
  # WRONG: overly specific field for a general config
  class DataLoaderConfig:
      mnist_dataset_config: MNISTDatasetConfig

  # CORRECT: general field matches config scope
  class DataLoaderConfig:
      dataset_config: DatasetConfig

  # BUT: when the config IS specific, the field should match
  class MNISTDataloaderConfig:
      mnist_dataset: MNISTDataset  # not "dataset: MNISTDataset"
  ```

### Instance disambiguation for generic types

When an instance's type name is too generic for the reader to understand its role in the containing class, follow these steps:
1. **Check ambiguity**: Is the type-derived name generic enough that a reader could reasonably imagine multiple distinct uses for it in this class? If not, the type-derived name is sufficient.
2. **Consider a hypothetical derived type**: If the name IS ambiguous, ask whether a specialized type (e.g., `InferenceSubsetDataset`) would ever need distinct behavior from the base. If yes, that hypothetical type's instance name is correct, and the type should be created when the behavioral need arises.
3. **Right-specialize if no type specialization is warranted**: Keep the type-derived base name on the left and add a disambiguating qualifier on the right (e.g., `subset_dataset_val`).

When choosing the qualifier in step 3, identify what the instance is **associated with** in the class (e.g., another attribute, a config field, a data source), then derive the qualifier from that thing's name with scoping drops applied. Do not reason about the instance's purpose, lifecycle, or conceptual content — those lead to qualifiers that describe usage rather than identity.

Step 3 is the more common case. Step 2 applies only when you can concretely imagine the specialized type needing different methods or state.

### Abbreviations and shorthands

- Use `Func` as the standard abbreviation for "Function" in names; do not mix `Function` and `Func`.
- Use `path` for fully qualified disk/S3 paths and `file` for bare filenames.
- Approved shorthands:
  - `variance` -> `var`
  - `Function` -> `Func`
- Do not invent repo-specific abbreviations; only use shorthands that a practitioner in the relevant domain would immediately recognize.

### Avoiding unnecessary indirection

- Do not introduce synonym/shorthand local variables unless needed for line-length or readability; otherwise access the original value directly. When a shorthand is justified, name it to match the original property or accessor — never introduce a synonym (e.g., use `loc`, not `mean`, for `distribution.loc`).
- If a variable represents a cohesive thing with multiple parts, pass the variable itself instead of passing its parts separately unless only a subset of the parts is needed.
- Avoid temporary variables when their values are only used to construct an object or call a function; compute the kwargs inline unless line length would become unreadable. When inlining expressions, always use explicit kwarg-assignment notation (e.g., `func(param=expr)`) so the inlined expression is self-documenting:
  ```python
  # WRONG — unnecessary temporaries
  x = compute_x()
  y = compute_y()
  result = MyThing(x=x, y=y)
  return result

  # CORRECT — inline when short enough
  result = MyThing(x=compute_x(), y=compute_y())

  return result
  ```
- Exception: when overriding a method, always capture the super's return value in a local and return it — do not discard it and access internal state instead.
- When constructing an object with multiple kwargs, assign it to a well-named variable and `return` that variable on a separate line.

### Function naming

- Name functions for what they do; avoid generic names like `forward` unless the method truly implements an established interface.
- When naming a function that returns a value, name it to describe what it returns, not how it computes the return value:
  ```python
  compute_example_results()     # CORRECT: describes the return value
  run_model_for_all_examples()  # WRONG: describes the mechanism
  ```
- When external libraries use incorrect/misleading names, correct them in our code with accurate naming that reflects the actual behavior.

### Property vs method naming

- When a method or property is iterated over (e.g., `for x in obj.thing`), its name must be a noun or noun phrase, not a verb. Code that reads as `for x in obj.validate` sounds like calling an action; `for x in obj.validation` reads as iterating over a collection.
- When a value is accessed as a property of an object rather than called as a function, prefer `@property` over a zero-argument method. Properties read as nouns (`obj.validation`); method calls read as actions (`obj.validate()`). Use a method only when the operation has meaningful side effects or takes parameters.
