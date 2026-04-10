# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from pconfigs import pconfig, pconfiged
from pconfigs.examples.environments.main import TrainerConfig


@pconfiged
class MyTrainer:
    config: MyTrainerConfig

    def is_root(self) -> bool:
        return self.config.environment.rank == 0


@pconfig(constructs=MyTrainer)
class MyTrainerConfig(TrainerConfig):
    pass


my_trainer_config = MyTrainerConfig(
    print_frequency_steps=10,
)

my_trainer = my_trainer_config.construct()
print("Is root:", my_trainer.is_root())
