# Hydra / OmegaConf

This page uses the same tiny “trainer” to show how Hydra/OmegaConf works compared to [pconfigs](pconfigs).

<strong><span style="font-size: 1.2em;">What to look for:</span></strong>

1. The command is not a single source of truth for the experiment (you often pass both an entry script and config selection/overrides).
1. Computed values use interpolations/resolvers (the YAML doesn’t show where a resolver is defined).
1. You run a script (`train.py`), not a config object.
1. The config points to types by string-ish paths (config groups), not Python symbols you import.
1. To get a full `lr_schedule` in the resolved config, you typically write a resolver in Python.
1. Hydra can print the composed config (and can resolve `${...}`), but it’s not the default “artifact” workflow like `pconfigs.print`.
1. As derived values get more complex (especially for nested submodule configs), YAML interpolations/resolvers become a small, implicit programming layer. Concrete problems include:
   - The YAML can “reach around” across the config tree (`${...}` paths), creating hidden dependencies that are hard to track and easy to break during restructuring.
   - Resolver logic lives in Python, but the YAML doesn’t say where it is defined; the config becomes less navigable and harder to refactor safely.
   - Complex derived values tend to have weaker validation and typing; errors often show up at resolve/instantiate time with stack traces that don’t explain the intended meaning.
   - “Printing the config” helps for values that live in the config tree, but if additional kwargs are computed in Python during instantiation, you must log/dump those runtime-resolved values separately.

## Typical invocation

```bash
python train.py experiment=second
```

## The current experiment config: `conf/experiment/second.yaml`

```yaml
defaults:
  - first
  - _self_

# Override only what changed.
trainer:
  base_lr: 1e-3
  steps: ${sub:${len:${.lr_schedule}},1}
```

This uses Hydra’s config composition: `second.yaml` includes `first.yaml`, then overrides a few values. The `_self_` entry makes sure values in this file win.

## The base experiment config: `conf/experiment/first.yaml`

```yaml
trainer:
  steps: 3
  base_lr: 3e-4
  total_steps: 6
  min_lr_ratio: 0.1
  grad_accum_steps: 4
  num_devices: 2

  # A simple computed value via a resolver (defined in Python).
  effective_batch_size: ${mul:${.grad_accum_steps},${.num_devices}}

  # A complex computed value via a resolver (also defined in Python).
  lr_schedule: ${lr_schedule:${.base_lr},${.total_steps},${.min_lr_ratio}}
```

## The printed config

Hydra can print the composed config (and can resolve `${...}` interpolations). Example output:

```yaml
experiment:
  trainer:
    steps: 5
    base_lr: 0.001
    total_steps: 6
    min_lr_ratio: 0.1
    grad_accum_steps: 4
    num_devices: 2
    effective_batch_size: 8
    lr_schedule:
    - 0.001
    - 0.0009140576474687264
    - 0.0006890576474687263
    - 0.00041094235253127365
    - 0.00018594235253127367
    - 0.0001
```

## The trainer script: `train.py`

```python
from __future__ import annotations

from dataclasses import dataclass

import hydra
import math
from omegaconf import OmegaConf


def make_lr_schedule(
    base_lr: float,
    total_steps: int,
    min_lr_ratio: float,
) -> list[float]:
    if (total_steps <= 0) or (not 0.0 <= min_lr_ratio <= 1.0):
        raise ValueError(f"Invalid schedule config: total_steps={total_steps} min_lr_ratio={min_lr_ratio}")

    min_lr = base_lr * min_lr_ratio
    cosine_denom = max(1, total_steps - 1)
    return [
        min_lr
        + (base_lr - min_lr) * 0.5 * (1.0 + math.cos(math.pi * step / cosine_denom))
        for step in range(total_steps)
    ]


@dataclass(frozen=True)
class TrainerConfig:
    steps: int
    base_lr: float
    total_steps: int
    min_lr_ratio: float
    grad_accum_steps: int
    num_devices: int
    effective_batch_size: int
    lr_schedule: list[float]


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg) -> None:
    # Resolvers used by the YAML live here, not in the config file.
    OmegaConf.register_new_resolver("mul", lambda a, b: int(a) * int(b), replace=True)
    OmegaConf.register_new_resolver("len", lambda x: len(x), replace=True)
    OmegaConf.register_new_resolver("sub", lambda a, b: int(a) - int(b), replace=True)
    OmegaConf.register_new_resolver(
        "lr_schedule",
        lambda base_lr, total_steps, min_lr_ratio: OmegaConf.create(
            make_lr_schedule(
                base_lr=float(base_lr),
                total_steps=int(total_steps),
                min_lr_ratio=float(min_lr_ratio),
            )
        ),
        replace=True,
    )

    trainer = OmegaConf.to_object(cfg.experiment.trainer)
    trainer_config = TrainerConfig(**trainer)

    for step in range(trainer_config.steps):
        lr = trainer_config.lr_schedule[step]
        print(f"step={step} lr={lr}")


if __name__ == "__main__":
    main()
```
