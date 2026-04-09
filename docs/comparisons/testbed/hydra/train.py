# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

import math
from dataclasses import dataclass

import hydra
from omegaconf import OmegaConf


def make_lr_schedule(
    *,
    base_lr: float,
    total_steps: int,
    min_lr_ratio: float,
) -> list[float]:
    if (total_steps <= 0) or (not 0.0 <= min_lr_ratio <= 1.0):
        raise ValueError(f"Invalid schedule config: total_steps={total_steps} min_lr_ratio={min_lr_ratio}")

    min_lr = base_lr * min_lr_ratio
    cosine_denom = max(1, total_steps - 1)
    return [
        min_lr + (base_lr - min_lr) * 0.5 * (1.0 + math.cos(math.pi * step / cosine_denom))
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


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg) -> None:
    trainer = OmegaConf.to_object(cfg.experiment.trainer)
    trainer_config = TrainerConfig(**trainer)

    print(f"effective_batch_size={trainer_config.effective_batch_size}")
    print(f"lr_schedule={trainer_config.lr_schedule}")
    for step in range(trainer_config.steps):
        lr = trainer_config.lr_schedule[step]
        print(f"step={step} lr={lr}")


if __name__ == "__main__":
    main()
