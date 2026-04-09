# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from pconfigs import pconfig, penv
from pconfigs.examples.environments.main import TrainerConfig, TrainerEnv


@penv(convention="uppercase")
class WithDefaultsTrainerEnv(TrainerEnv):
    world_size: int = 1
    rank: int = 0


@pconfig
class WithDefaultsTrainerConfig(TrainerConfig):
    environment: WithDefaultsTrainerEnv  # Environments are always called 'environment'


trainer_config = WithDefaultsTrainerConfig(
    print_frequency_steps=10,
)
