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

from pconfigs import pconfig, pconfiged, pdefaults
from pconfigs.pinnable import Pinned, pproperty


@pconfiged(runnable=True)
class Trainer:
    config: TrainerConfig

    def main(self, *args, **kwargs) -> int:
        for step in range(self.config.steps):
            lr = self.config.lr_schedule[step]
            print(f"step={step} lr={lr}")

        return 0


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
            min_lr + (self.base_lr - min_lr) * 0.5 * (1.0 + math.cos(math.pi * step / cosine_denom))
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
