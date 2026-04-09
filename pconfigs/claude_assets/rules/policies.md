---
description: "Repo-wide coding policies, style rules, pconfig specialization/modification rules, and formatting conventions"
---

## Repo-wide policies

### The two most important rules

1. After making code changes, always double-check for adherence to all project rules. Repeat this check until the code adheres to the project rules.
2. If a user request would violate an existing rule, push back and explain which rule it conflicts with before making the change. Only proceed if the user explicitly overrides after understanding the conflict.

### General coding policies

- Always follow PEP 8 style unless a specific repo coding rule requires a deviation.
- When using an `if/elif` chain, add an `else` that raises if it is not expected:
  ```python
  # WRONG — missing else
  if mode is Mode.Train:
      handle_train()

  elif mode is Mode.Eval:
      handle_eval()

  # CORRECT
  if mode is Mode.Train:
      handle_train()

  elif mode is Mode.Eval:
      handle_eval()
  else:
      raise ValueError(f"Unhandled mode: {mode}")
  ```
- When implementing if/elif/else chains that check config options, use enums (@penum) to define the scope of names. Do not use raw strings:
  ```python
  # WRONG: raw strings
  if self.config.mode == "train":
      ...

  # CORRECT: use @penum
  @penum
  class Mode:
      Train = "train"
      Eval = "eval"

  if self.config.mode is Mode.Train:
      ...
  elif self.config.mode is Mode.Eval:
      ...
  else:
      raise ValueError(f"Unhandled mode: {self.config.mode}")
  ```
- When constructing external classes, create pconfig wrappers for those objects and build them via `.construct()`.
- Code comments should very rarely be used. Never write a comment when the name of a function, class, method, or variable already expresses the same information. If a comment seems needed, that indicates a naming problem: rename the code element instead.
- When breaking a coding rule is justified by technical constraints (which must be vanishingly rare), add a brief comment near the offending code explaining the justification. The comment should state what rule is being broken and why. The statement must be logical without inferred reasons.
- Do not monkey-patch objects by assigning methods or attributes at runtime. To modify behavior, subclass and override properly.
- Do not extract short helper functions (3-7 lines) unless they are reused in multiple places. A single-use, short helper adds indirection without benefit — inline the code instead.
- When designing object interfaces, minimize what a caller must know. If an object computes a result internally, do not require the caller to wire that result back into the object's next method call.
- Minimize the number of valid forms a parameter can take. A parameter should accept exactly one type with no special-case sentinel values.
- The single-form-per-parameter rule extends to tensor and array shapes: a function that accepts a `Tensor` should require exactly one shape convention (e.g., always 4D batched `[B, C, H, W]`), not dynamically handle both batched and unbatched inputs.
- When a parameter needs a "not set" or "disabled" state, widen the type to `Optional[T]` and use `None`. Do not reserve a value within the existing type (e.g., `0` or `-1`) as a sentinel.
- Only define a type in the file where it is used. Do not define types in a base module for the sole purpose of being imported by a derived module.
- Internal class methods that perform computation should accept their data dependencies as parameters rather than implicitly reading them from `self`. Framework callbacks whose signatures are dictated by an external interface are exempt.
  - This rule applies to methods that are only called within the class itself. Public interface methods are exempt.
  - A method should never accept a parameter whose value comes from `self.config`; config values should always be read from `self.config` directly.

### Style & structure

- Keep modules split by responsibility:
  - `modules/` define pconfig types, pconfiged classes, defaults.
  - `pconfigs/` (or similar) defines config instances (experiments), not new types.
- Experiment subtrees are config-instance directories, marked by `__pconfigs__.py` sentinels; treat them as entrypoints that wire configs to systems.
- Do not use default values for function or method parameters:
  ```python
  # WRONG
  def compute_loss(self, predictions: Tensor, reduction: str = "mean") -> Tensor:

  # CORRECT
  def compute_loss(self, predictions: Tensor, reduction: str) -> Tensor:
  ```
- Never use optional constructor kwargs.
- Never use `*args` or `**kwargs` to define flexible interfaces. All method signatures must have explicit, named parameters.
- Never implement dispatch functions or registries that select types or objects by name, string, dictionary, or `isinstance` checks. If multiple config types need to produce different objects, use pconfiged polymorphism (`@pconfig(constructs=...)` + `.construct()`), not a central function that branches on the config's type.
- Avoid leading underscores for instance attributes or method names unless there is a clear privacy need.
- When one @pconfiged object needs to instantiate another @pconfiged object:
  - The first object's config should have a field for the second object's config.
  - The first object's constructor should call `.construct()` on the second object's config.

### pconfig specialization rules (non-negotiable)

These rules apply whenever one pconfig file specializes another. This includes both (a) deriving a new pconfig/pconfiged class from a previous one, and (b) creating a pconfig instance file that uses another instance file as its base config.

Before applying the specialization steps below, determine the relationship between the new config and existing configs in the same directory:
- **Sibling**: The new config varies the same parameter(s) as an existing config at the same level (e.g., both change LoRA rank but to different values). Create the new file as a sibling in the same directory, importing from the shared parent's `base.py`. Do not restructure the existing sibling.
- **Child**: The new config adds a qualitatively new conceptual layer on top of an existing config (e.g., adding validation to a config that lacked it). Apply the specialization steps below to make the existing config the new parent.

A sibling relationship is indicated when the new config would override the same fields as an existing sibling but with different values. A child relationship is indicated when the new config introduces new structure (new sub-configs, new fields) that refines the existing config's concept.

The specialization steps below apply only to child relationships. In this example, the previous file is `path/to/previous.py`.
1. Create a new directory called `path/to/previous/`
2. Move `path/to/previous.py` to `path/to/previous/base.py`
3. Create `path/to/previous/__init__.py`
4. Add to that `__init__.py` the following code, verbatim: `from .base import *`
5. Create a new file `path/to/previous/shorthand_name.py` where "shorthand_name" has at most two `_` characters and no more than 25 characters, summarizing the specialization.
6. Add the new specialized code in `shorthand_name.py` by importing from `path/to/previous/base.py`.

- Never put significant code in `__init__.py` files; only use them for the specialization step above (exactly `from .base import *`).
- `__pconfigs__.py` sentinel files must be empty (no imports or other code).

### pconfig instance file operations (non-negotiable)

- Never rename or move existing pconfig instance files. Renaming breaks journal dotpath references (notebook entries, questions, conclusions) and S3 run paths that cannot be perfectly maintained. Only rename a file that was just created in the current session and has never been run or referenced anywhere.

### pconfig code modifications (non-negotiable)

When adding or modifying the functionality of existing code, never make changes that would cause existing runnable pconfig instances to function differently. Follow these steps to choose the right modification strategy:

1. Ask the user: has the experiment config produced valid results, or has it only crashed / OOM'd / been misconfigured?
   - Never produced valid results → modify the config file in place (see "Debugging failed experiment configs" below). Stop here.
   - Produced valid results → continue to step 2.
2. Is the change a small computational variation (e.g., clamping a value, adding an optional flag)?
   - Yes → add a new config parameter with a default that preserves existing behavior, creating a new optional code path through an existing class method.
   - No → continue to step 3.
3. Can the new behavior be encapsulated in a helper object that the existing class calls into?
   - Yes → add an optional sub-config field (defaulting to `None` or an identity implementation) that constructs a helper object. The existing class delegates to the helper rather than adding conditional branches. This keeps the new code outside the existing class without requiring a derived class.
   - No → continue to step 4.
4. Does the change require new methods, different control flow, or different state management?
   - Yes → create a new subclass and overload the method you need to modify. Follow the pconfig specialization rules.
   - Unclear → ask the user which of the three strategies (config parameter, sub-config helper, or subclass) they prefer.

### Debugging failed experiment configs

- The pconfig specialization and code modification rules above apply only to experiments that have produced valid results. When an experiment config has never successfully run (e.g., it crashed, OOM'd, or was misconfigured), the config file may be modified in place for debugging.
- Do not create new specialization files (e.g., `sanity.py`, `debug.py`) in the experiment tree for temporary debugging.
- When debugging requires temporarily disabling config lines that represent the intended final configuration, comment those lines out instead of deleting them.
- When debugging requires adding temporary config overrides (e.g., `max_steps=2`), add them directly in the config file. Once the experiment succeeds, remove the temporary overrides and uncomment the intended config.

### Formatting conventions

- Always add an extra blank line after returning from an indented block inside a function or method.
- Always add an extra blank line before return statements, unless the return is the first statement in its block.
- Avoid extra blank lines before `return`, `elif`, or `else` when the preceding line is effectively a single token (e.g., a closing `)` or `]`).
- In `for` loops, prefer iterating directly over the collection. When an index is also needed, use `enumerate` rather than `for i in range(len(...))`.
- In `if/elif/else` chains, include a blank line between `if` and `elif` blocks, but do not insert a blank line before a short `else` block:
  ```python
  if condition_a:
      handle_a()

  elif condition_b:
      handle_b()

  elif condition_c:
      handle_c()
  else:
      raise ValueError("Unexpected condition")
  ```

### Rule adherence audit

After writing or modifying code, audit every changed line against the project rules before presenting the result. When the changes include pconfigs code (configs, pconfiged classes, pproperties, or experiment instance files), run the pconfigs-review skill as part of this audit. For each violation found:
1. Fix it immediately.
2. After fixing all violations, tell the user which rules were violated and suggest concrete rule amendments that would have prevented the mistake. The user will decide whether to adopt the amendments.
