# Optional subconfigs

A subconfig can be marked optional, so the consuming class does not need to branch on its presence.

(subsec-use-optionalconfig-and-noneconfig)=
## Use `OptionalConfig` and `NoneConfig`.

Annotate the field with `OptionalConfig[T]`, and call `.construct()` uniformly:
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
`NoneConfig.construct()` returns `None`.

(subsec-turn-the-subconfig-on-and-off)=
## Turn the subconfig on and off.

Pass `NoneConfig` to disable, and an `EvaluatorConfig(...)` instance to enable:
```python
system_without_eval = SystemConfig(evaluator_config=NoneConfig).construct()
system_with_eval    = SystemConfig(evaluator_config=EvaluatorConfig(...)).construct()
```
`NoneConfig` is a module-level singleton---like Python's `None`, it is passed as a value, not constructed.

(subsec-bare-union-form)=
## Bare union form.

`OptionalConfig[EvaluatorConfig]` evaluates to `Union[EvaluatorConfig, OptionalConfig]`. The bare union form is equivalent:
```python
@pconfig(constructs=System)
class SystemConfig:
    evaluator_config: EvaluatorConfig | OptionalConfig
```

(subsec-why-not-optional)=
## Why not `Optional[T]`?

`Optional[T]` forces every reader to branch on `None`:
```python
self.evaluator = (
    self.config.evaluator_config.construct()
    if self.config.evaluator_config is not None
    else None
)
```
The branch is repeated wherever the field is read, and is easy to forget. `OptionalConfig` removes it.
