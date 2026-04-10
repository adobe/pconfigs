# pconfigs

This page uses a tiny “trainer” to show how pconfigs works compared to other systems.

<strong><span style="font-size: 1.2em;">What to look for:</span></strong>

1. The command line specifies a single source of truth that defines the experiment: the config.
1. The config points to where computed values are defined—no “where is this defined?” mystery.
1. You run the experiment config with a standard command, not a separate script you have to find.
1. The config imports `TrainerConfig` as a Python symbol, so its definition is explicit and IDE-navigable.
1. The learning-rate schedule lives in `TrainerConfig.lr_schedule`, next to the inputs it uses.
1. You can print the resolved config values before running (`python -m pconfigs.print ...`), including derived values (`lr_schedule`).

## Typical invocation

```bash
python -m pconfigs.run project.experiments.second.config
```

An “experiment” is just a **Python object** (typically named `config`) that can be imported like any other symbol. A generic runner (`pconfigs.run`) can accept a dotted path to that object (e.g. `project.experiments.second.config`).

## The current experiment config

```python
from project.experiments.first import config as first_expr  # Some previous experiment.
from project.modules.trainer import TrainerConfig

config = TrainerConfig(
    first_expr,       # Use all values from first experiment.
    base_lr=1e-3,
    steps=len(first_expr.lr_schedule) - 1,
)
```

## The base experiment config

```python
from project.modules.trainer import TrainerConfig

config = TrainerConfig(
    steps=3,
    base_lr=3e-4,
    total_steps=6,
    min_lr_ratio=0.1,
    grad_accum_steps=4,
    num_devices=2,
)
```

## The printed config

```bash
python -m pconfigs.print project.experiments.second.config
```
The **printed** output is code:

```python
from project.modules.trainer import TrainerConfig, Trainer

# NOTE: This code is not intended to run. It is for reading and looking up type definitions.
# If you want to run or inspect these objects, import the config from where it is defined.

TrainerConfig(
    constructable_type=Trainer,  # ClassVar (omit from config)
    steps=5,
    base_lr=0.001,
    total_steps=6,
    min_lr_ratio=0.1,
    grad_accum_steps=4,
    num_devices=2,
    effective_batch_size=8,  # Pinned (omit from config)
    lr_schedule=[
        0.001,
        0.0009140576474687264,
        0.0006890576474687263,
        0.00041094235253127365,
        0.00018594235253127367,
        0.0001,
    ],  # Pinned (omit from config)
)
```

## The trainer "script": `modules/trainer.py`

```python
from __future__ import annotations

import math

from pconfigs import pconfig, pconfiged, pdefaults
from pconfigs.pinnable import Pinned, pproperty


@pconfiged(runnable=True)
class Trainer:
    config: TrainerConfig

    def main(self, *args, **kwargs):
        for step in range(self.config.steps):
            lr = self.config.lr_schedule[step]
            print(f"step={step} lr={lr}")


@pconfig(constructs=Trainer)
class TrainerConfig:
    steps: int
    base_lr: float
    total_steps: int
    min_lr_ratio: float
    grad_accum_steps: int
    num_devices: int

    effective_batch_size: Pinned[int]
    lr_schedule: Pinned[list[float]]

    @pproperty
    def effective_batch_size(self) -> int:
        return self.grad_accum_steps * self.num_devices

    @pproperty
    def lr_schedule(self) -> list[float]:
        if (self.total_steps <= 0) or (not 0.0 <= self.min_lr_ratio <= 1.0):
            raise ValueError("Bad lr_schedule.")

        min_lr = self.base_lr * self.min_lr_ratio
        cosine_denom = max(1, self.total_steps - 1)

        return [
            min_lr
            + (self.base_lr - min_lr)
            * 0.5
            * (1.0 + math.cos(math.pi * step / cosine_denom))
            for step in range(self.total_steps)
        ]


pdefaults += TrainerConfig(
    steps=3,
    base_lr=3e-4,
    total_steps=6,
    min_lr_ratio=0.1,
    grad_accum_steps=4,
    num_devices=2,
    effective_batch_size=Pinned,
    lr_schedule=Pinned,
)
```

