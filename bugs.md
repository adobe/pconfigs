# Known Bugs

## Pinned field inheritance from base config

**Status:** Open

When a derived `@pconfig` class re-declares a field from the base class as `Pinned[T]`
(either via a `@pproperty` or via `pdefaults += DerivedConfig(field=Pin(value))`), constructing
the derived config from a base config instance fails:

```python
@pconfig(constructs=Base)
class BaseConfig:
    mode: Mode

@pconfig(constructs=Derived)
class DerivedConfig(BaseConfig):
    mode: Pinned[Mode]

pdefaults += DerivedConfig(mode=Pin(Mode.Eval))

base_config = BaseConfig(mode=Mode.Train)
DerivedConfig(base_config)  # raises ValueError: Cannot set a pinned field
```

The copy-construction mechanism tries to copy `mode` from `base_config` into `DerivedConfig`
before the `Pin(Mode.Eval)` default is applied, and the setter throws because the field
is declared `Pinned`.

**Expected behavior:** Fields declared `Pinned[T]` in a derived config should be skipped
during base-config copying. The pinned value (from pdefaults or pproperty) should win.

**Same failure occurs with `@pproperty`:** The pproperty installs a setter that also calls
`_throw_if_pinned`, so passing a base config with a value for that field fails identically.

**Workaround:** Call the sub-object's eval/train method directly at runtime rather than
expressing it as a config field override.
