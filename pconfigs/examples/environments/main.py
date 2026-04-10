# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from pconfigs import pconfig, pdefaults, penv


@penv(convention="uppercase")
class TrainerEnv:
    world_size: int
    rank: int


@pconfig
class TrainerConfig:
    environment: TrainerEnv  # Environments are always called 'environment'
    print_frequency_steps: int


trainer_config = TrainerConfig(
    print_frequency_steps=10,
)
