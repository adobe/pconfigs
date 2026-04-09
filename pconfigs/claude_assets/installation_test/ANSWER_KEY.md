# Rule-Adherence Answer Key

Score the agent's answers in `.cursor/installation_test/answers/` against the criteria below.

## Instructions

1. For each question Q<NN>, read the answer from `.cursor/installation_test/answers/q<NN>.md`
   and write the score to `.cursor/installation_test/scores/s<NN>.md`.
2. Do NOT modify any files in `.cursor/installation_test/answers/`. Score the original
   answers as-is.
3. For each question, check every criterion. Mark `[x]` if met, `[ ]` if not.
   - Apply each criterion literally. If the answer does not meet the
     criterion as written, mark `[ ]`.
   - Do not interpret criteria charitably or infer intent.
   - Do not add caveats, footnotes, or disclaimers to justify a `[x]` mark.
     Each criterion is binary: met or not met.
4. A question passes only when ALL criteria are `[x]`.
5. Write each `s<NN>.md` file using diff code blocks so that failures render in red:
   - List passing criteria as normal markdown: `- [x] criterion`
   - Wrap ALL failed criteria and the `**Result:** FAIL` line in a `diff` code
     block, prefixing each line with `- ` (the diff deletion marker):

   Passing example (`s01.md`):
   ```
   - [x] criterion 1
   - [x] criterion 2
   **Result:** PASS
   ```

   Failing example (`s02.md`):
   ````
   - [x] criterion 1
   ```diff
   - [ ] criterion 2
   - **Result:** FAIL
   ```
   ````

6. After writing all `s<NN>.md` files, create `.cursor/installation_test/TEST_SCORE.md`.
   Read each `s<NN>.md` to determine PASS/FAIL and write the summary as:

   ```
   ## Summary: <passed>/<total> passed

   | Question | Result |
   |----------|--------|
   | Q01      | PASS   |
   | Q02      | FAIL   |
   | ...      | ...    |
   ```

## Important: scoring must happen in a separate conversation

The agent that wrote the answers must NOT score its own work.
Run the scoring step in a new conversation that has no memory of writing
the answers. Self-scoring creates a conflict of interest that leads to
generous interpretations and rationalized passes.

---

## Part 1: Does the agent see the rules?

### Q01: Configurable image resizer
- Uses `@pconfiged` on the runtime class?
- Uses `@pconfig(constructs=ImageResizer)` on the config class?
- Config class is named `ImageResizerConfig`?
- `pdefaults += ...` appears outside the class body?

---

## Part 2: Core configuration design

### Q02: Configurable DataReader class
- `@pconfiged` class has a `config: DataReaderConfig` attribute?
- `__init__` takes no arguments (or is omitted entirely)?
- Config class uses `@pconfig(constructs=DataReader)`?
- `pdefaults` defined separately from the config class body?

---

### Q03: Config value access in methods
- Method body reads `self.config.batch_size` at point of use?
- Does NOT assign `self.batch_size = self.config.batch_size` in `__init__` or elsewhere?

---

### Q04: Sub-config usage across methods
- Calls `self.config.transform_config.construct()` in `__init__` (not inside `read`)?
- Assigns the result to `self.transform` (not `self.data_transform` or another name)?

---

### Q05: Sub-config field override
- Passes `base` as the first positional argument to the outer config constructor?
- Passes `base.sub_config` as the first positional argument to the inner `SubConfig()` call?
- Does NOT use `pdefaults(SubConfig)` inside the construction block?

---

### Q06: Type definition placement
- Refuses or pushes back against putting the `@pconfig` type in that directory?
- Explains that `__pconfigs__.py` directories contain only config instances, not type definitions?

---

### Q07: Derived class creation
- Creates directory `genrg/modules/plotter/`?
- Moves `plotter.py` to `genrg/modules/plotter/base.py`?
- Creates `genrg/modules/plotter/__init__.py` containing exactly `from .base import *`?
- New derived-class file has a shorthand name with at most 2 underscores and at most 25 characters (e.g., `heatmap.py`)?
- New file imports from `.base` or `genrg.modules.plotter.base`?

---

### Q08: Modifying an existing method
- Asks whether the experiment has produced valid results before making changes?
- Does NOT immediately edit the method?

---

### Q09: Model selection by name
- Refuses to build the registry (pushes back, citing the rule against registries)?
- Proposes the pconfigs alternative: let configs carry the constructable type?

---

### Q10: Finding a config field value
- Shows `python -m pconfigs.print genrg.pconfig.my_experiment.config` (or equivalent)?
- Pipes to a file or greps the output (does NOT open source files to trace values manually)?

---

### Q11: Configurable torch.optim.Adam
- Uses `@pconfig(mocks=torch.optim.Adam)` or `@pconfig(mocks=Adam)` (not `calls=`)?
- Config class named `AdamConfig` (not `AdamFunc`, not `AdamOptimizerConfig`)?
- Constructed via `.construct(params=...)` (not invoked directly like a `calls=` config)?

---

### Q12: Machine-specific data path
- Uses `@penv(convention="uppercase")`?
- The field on the system config is named exactly `environment`?
- `data_dir` default is `None` (not `""` or `Required`)?
- Env class is defined immediately above the config class that uses it?

---

## Part 3: Design patterns and naming

### Q13: Full module with mode switching
- Uses `@penum` for the mode (not raw strings)?
- Uses `is` comparison (not `==`) when checking the mode?
- Has `else: raise ValueError(...)` (or similar) in the if/elif chain?
- No default parameter values on any method?
- Config values read from `self.config` at point of use (not cached on `self`)?
- Sub-config constructed in `__init__` and reused in methods?
- Blank line between `if` and `elif` blocks?

---

### Q14: Mode-based return values
- Defines a `@penum` type for the mode (not raw strings)?
- Uses `is` (not `==`) to compare enum values?
- Ends with `else: raise ValueError(...)` or equivalent?
- Blank line between `if` and `elif` blocks; no blank line before `else`?

---

### Q15: Normalize method signature
- Method signature has no `= value` defaults (e.g., NOT `mode: str = "standard"`)?
- Method signature has no `*args` or `**kwargs`?

---

### Q16: Configurable torch.linspace
- Uses `@pconfig(calls=torch.linspace)` (not `mocks=`)?
- Config class named `LinspaceFunc` (not `LinspaceConfig` or `TorchLinspaceFunc`)?
- Example shows direct invocation (not `.construct()`)?

---

### Q17: Sub-config construction assignment
- Assigns to `self.loader` (dropping the `_config` suffix from `loader_config`)?
- Does NOT use `self.batch_loader`, `self.loader_config`, or another variant?

---

### Q18: String processing method
- Uses one consistent word for the string throughout (e.g., `message`)?
- Does NOT introduce synonyms like `text`, `msg`, `content`, `string`?

---

### Q19: Logger wrapper naming
- Proposed name describes what the class does (e.g., `ErrorOnlyLogger`)?
- Does NOT use a subjective name like `MinimalLogger`, `QuietLogger`, `CleanLogger`?

---

### Q20: Schedule variable naming
- Names put the general category first: `schedule_warmup` and `schedule_decay`?
- Does NOT reverse the order: `warmup_schedule`, `decay_schedule`?

---

### Q21: Metric base class naming
- Proposes `Metric` (not `ValidationMetric`)?
- Recognizes that "validation" is redundant with the containing class context?

---

### Q22: Filtered list variable naming
- Name includes a noun after the participle (e.g., `filtered_predictions`)?
- Does NOT propose a bare participle like `filtered`?

---

### Q23: Collection iteration with error handling
- Uses direct iteration (`for item in items:`) rather than index-based (`for i in range(len(items))`)?

---

## Part 4: Advanced configuration patterns

### Q24: Configurable loss function
- Config field for the loss is NOT typed as `Callable`, `Type[...]`, or a raw function reference?
- Uses `@pconfig(calls=...)` for functional losses OR `@pconfig(mocks=...)` for class-based losses (e.g., `torch.nn.L1Loss`)?
- Config class naming matches the approach: `Func` suffix for `calls=` (e.g., `L1LossFunc`), `Config` suffix for `mocks=` (e.g., `L1LossConfig`)?

---

### Q25: Derived config field
- Uses `@pproperty` for the computed `log_dir`?
- `log_dir` field is typed as `Pinned[str]`?
- `pdefaults` sets `log_dir=Pinned` (the sentinel, not a concrete value)?
- Reads `output_dir` via `self.output_dir` (since `output_dir` has no associated `@pproperty`, `pinputs` is not needed)?
- Does NOT require users to set `log_dir` independently?

---

### Q26: Adding gradient accumulation
- Adds a new config field (e.g., `accumulation_steps`) with a default that preserves existing behavior (e.g., `1`)?
- Does NOT create a derived class for this small computational variation?
- Existing experiment configs continue to work without modification?

---

### Q27: Per-run learning rate
- Does NOT use `argparse`, `click`, `sys.argv`, or other CLI argument parsing?
- Describes or shows a config instance file approach (learning rate is set in the config file)?
- References `python -m pconfigs.run` for launching (or equivalent)?

---

### Q28: Making hardcoded values configurable
- Does NOT add `mean` and `std` as constructor parameters to `ImagePreprocessor`?
- Does NOT use `**kwargs` or `*args` to forward parameters?
- Uses a sub-config for the normalizer (e.g., `normalizer_config: NormalizerConfig`)?
- Normalizer is constructed via `.construct()` on the sub-config?

---

### Q29: Reproducing experiment settings
- Does NOT simply trust the colleague's stated values as sufficient for reproduction?
- Identifies that the config file in the repo is the source of truth for experiment settings?
- References git history or the config dotpath to locate the exact configuration?
- Mentions using `pconfigs.print` (or equivalent) to resolve the full settings?

---

### Q30: pinputs in a pproperty
- The pproperty reads the user-provided module config via `pinputs(self).module_config` (not `self.module_config`)?
- Copies from the user-provided config as the first positional argument (e.g., `InputConfig(inputs, ...)`)?
- Pins `checkpoint_dir` using `Pin(...)` (e.g., `checkpoint_dir=Pin(self.base_dir + '/checkpoints')`)?
- Reads `base_dir` via `self.base_dir` (not `pinputs`), since `base_dir` has no pproperty?

---
