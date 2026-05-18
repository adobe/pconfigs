# Optional subconfigs

Sometimes a submodule is optional---a system can run with or without it. `OptionalConfig` and `NoneConfig` let you express this without forcing the consuming class to branch at every use site. The split mirrors Python's own `Optional[T]`/`None` distinction: `OptionalConfig` is the *type* used in annotations, and `NoneConfig` is the singleton *value* that callers pass when the subconfig is absent.

(subsec-the-problem-optional-subconfig-and-the-ternary)=
## The problem: `Optional[T]` and the ternary.

Without `OptionalConfig`, an optional subconfig is typically expressed with `Optional[T]`, and every reader must branch:
```python
from typing import Optional

from pconfigs import pconfig, pconfiged

@pconfig(constructs=System)
class SystemConfig:
    evaluator_config: Optional[EvaluatorConfig]


@pconfiged
class System:
    config: SystemConfig

    def __init__(self):
        self.evaluator = (
            self.config.evaluator_config.construct()    # Construct the evaluator...
            if self.config.evaluator_config is not None
            else None                                   # ...or do not.
        )
```
The branch is repeated wherever the optional subconfig is read, and is easy to forget.

(subsec-use-optionalconfig-and-noneconfig)=
## Use `OptionalConfig` and `NoneConfig`.

Replace the `Optional[T]` annotation with `OptionalConfig[T]`, and let the consuming class call `.construct()` uniformly:
```python
from pconfigs import OptionalConfig, NoneConfig, pconfig, pconfiged

@pconfig(constructs=System)
class SystemConfig:
    evaluator_config: OptionalConfig[EvaluatorConfig]   # Equivalent to ``EvaluatorConfig | OptionalConfig``.


@pconfiged
class System:
    config: SystemConfig

    def __init__(self):
        self.evaluator = self.config.evaluator_config.construct()   # ``None`` when ``NoneConfig`` was passed.
```
`NoneConfig.construct()` returns `None`, so the consuming class does not need to know which case it received.

(subsec-turn-the-subconfig-on-and-off)=
## Turn the subconfig on and off.

Callers turn the subconfig off by passing `NoneConfig`, and on by passing a real `EvaluatorConfig(...)`:
```python
system_without_eval = SystemConfig(evaluator_config=NoneConfig).construct()
system_with_eval    = SystemConfig(evaluator_config=EvaluatorConfig(...)).construct()
```
`NoneConfig` is a module-level singleton instance of `OptionalConfig`---like Python's `None`, it is passed as a value, not constructed.

(subsec-bare-union-form)=
## Bare union form.

`OptionalConfig[EvaluatorConfig]` is a typing shortcut that evaluates to `Union[EvaluatorConfig, OptionalConfig]`---the same way `Optional[T]` evaluates to `Union[T, None]`. The bare union form is equivalent:
```python
@pconfig(constructs=System)
class SystemConfig:
    evaluator_config: EvaluatorConfig | OptionalConfig
```
Either form is acceptable; pick whichever reads more clearly at the use site.
