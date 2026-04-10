# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from os import path
from typing import List

from pconfigs import Pinned, pconfig, pconfiged, pdefaults, penv, pproperty


class Trainer:
    def __init__(self, devices: List[int]):
        self.devices = devices


@penv(convention="uppercase")
class LTrainerEnvironment:
    local_rank: int = 0


@pconfiged(mock=True)
class LTrainer(Trainer):
    config: LTrainerConfig


@pconfig(constructs=LTrainer)
class LTrainerConfig:
    environment: LTrainerEnvironment
    devices: Pinned[List[int]]

    @pproperty
    def devices(self) -> List[int]:
        return [self.environment.local_rank]


pdefaults += LTrainerConfig(
    devices=Pinned,
)

config = LTrainerConfig()

assert config.devices == [0]

print(f"{path.basename(__file__)}  Environment configs don't get set to Required when using mock.")
