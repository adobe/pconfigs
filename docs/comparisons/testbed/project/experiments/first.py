# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from project.modules.trainer import TrainerConfig

config = TrainerConfig(
    steps=3,
    base_lr=3e-4,
    total_steps=6,
    min_lr_ratio=0.1,
    grad_accum_steps=4,
    num_devices=2,
)
