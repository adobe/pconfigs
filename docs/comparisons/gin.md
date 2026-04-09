# Gin

This page uses a tiny “trainer” to show how Gin works compared to [pconfigs](pconfigs).

<strong><span style="font-size: 1.2em;">What to look for:</span></strong>

1. The command references muliple things rather than a single source of truth for the experiment.
1. The `.gin` file calls `@...()`, but it doesn’t show where those functions are defined.
1. The user must know where the train script is, and which config files can work with it.
1. The gin config doesn't specify where `TrainerConfig` is defined.
1. The `lr_schedule` lives in Python, so you must jump between the `.gin` files and `train.py`.
1. The `lr_schedule` for the experiment is not printed—you can't figure out what it is.
1. For more complex experiments, “derived values” (submodule kwargs, schedules, etc.) tend to turn the config into a small, implicit programming layer (`@...()` plus cross-scope lookups). Concrete problems include:
   - There are no clear scoping rules a reader can rely on; values can silently depend on distant bindings.
   - “Go to definition” is weak: the config references `@...()` but doesn’t tell you where the function lives, and refactors/renames can break configs indirectly.
   - There’s no type checking at the config boundary; mistakes show up late (at runtime) with error messages that usually point into Gin internals rather than your intent.
   - The “final resolved config” is not an artifact you can easily print and review (especially for derived lists/structures), so it’s hard to confirm what will actually run.

## Typical invocation

```bash
python train.py --gin_file experiments/second.gin
```

## The current experiment config: `experiments/second.gin`

```text
# This file names its base experiment via `include`, then overrides only what changed.

include "experiments/first.gin"

# Override only what changed.
TrainerConfig.base_lr = 1e-3
TrainerConfig.steps = 5

# Bind the computed values so it’s obvious what they are.
# (Gin does not show where these `@...()` functions are defined.)
TrainerConfig.effective_batch_size = @compute_effective_batch_size()
TrainerConfig.lr_schedule = @make_lr_schedule()
```

## The base experiment config: `experiments/first.gin`

```text
# (Shown for comparison to `experiments/second.gin`.)

TrainerConfig.steps = 3
TrainerConfig.base_lr = 3e-4
TrainerConfig.total_steps = 6
TrainerConfig.min_lr_ratio = 0.1
TrainerConfig.grad_accum_steps = 4
TrainerConfig.num_devices = 2

TrainerConfig.effective_batch_size = @compute_effective_batch_size()
TrainerConfig.lr_schedule = @make_lr_schedule()
```

## The trainer script: `train.py`

```python
from __future__ import annotations

from dataclasses import dataclass

import gin
from absl import app, flags
import math


FLAGS = flags.FLAGS
flags.DEFINE_multi_string("gin_file", None, "Gin config files to load.")
flags.DEFINE_multi_string("gin_param", None, "Gin parameter bindings (overrides).")


@gin.configurable
def compute_effective_batch_size(
) -> int:
    grad_accum_steps = gin.query_parameter("TrainerConfig.grad_accum_steps")
    num_devices = gin.query_parameter("TrainerConfig.num_devices")
    return int(grad_accum_steps) * int(num_devices)


@gin.configurable
def make_lr_schedule(
) -> list[float]:
    base_lr = float(gin.query_parameter("TrainerConfig.base_lr"))
    total_steps = int(gin.query_parameter("TrainerConfig.total_steps"))
    min_lr_ratio = float(gin.query_parameter("TrainerConfig.min_lr_ratio"))

    if (total_steps <= 0) or (not 0.0 <= min_lr_ratio <= 1.0):
        raise ValueError(f"Invalid schedule config: total_steps={total_steps} min_lr_ratio={min_lr_ratio}")

    min_lr = base_lr * min_lr_ratio
    cosine_denom = max(1, total_steps - 1)
    return [
        min_lr
        + (base_lr - min_lr) * 0.5 * (1.0 + math.cos(math.pi * step / cosine_denom))
        for step in range(total_steps)
    ]


@gin.configurable
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


def train(trainer_config: TrainerConfig) -> None:
    for step in range(trainer_config.steps):
        lr = trainer_config.lr_schedule[step]
        print(f"step={step} lr={lr}")


def main(argv: list[str]) -> None:
    del argv

    gin.parse_config_files_and_bindings(
        config_files=FLAGS.gin_file,
        bindings=FLAGS.gin_param,
    )
    trainer_config = TrainerConfig()
    train(trainer_config=trainer_config)


if __name__ == "__main__":
    flags.mark_flag_as_required("gin_file")
    app.run(main)
```

