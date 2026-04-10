# Configs and Pins

Pinned fields indicate which values are user-overridable. Use `Pin(value)` in defaults; use `Pinned` at the call site to request the default.

```python
from pconfigs.pinnable import pconfig, Pinned, Pin, pdefaults, pproperty

@pconfig
class ModelConfig:
    x: float
    y: float
    z: Pinned[float]

    @pproperty
    def x(self) -> float:  # computed, not pinned
        return self.y * 2

# Declare defaults once
pdefaults += ModelConfig(
    y=2.0,
    z=Pin(3.0),    # mark as pinned; may be overridden by the user
)

# Consume defaults
cfg = pdefaults(ModelConfig)
assert cfg.x == 4.0
assert cfg.z == 3.0

# User overrides only for pinned fields
cfg2 = ModelConfig(y=10.0, z=Pinned)  # ask for default pin value
assert cfg2.x == 20.0                 # recomputed from y
assert cfg2.z == 3.0                  # from defaults
```
