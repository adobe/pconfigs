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

from pconfigs.config_runner import ConfigRunnable
from pconfigs.pinnable import pconfig, pconfiged


@pconfiged(runnable=True)
class WillBeRunnable:
    config: WillBeRunnableConfig


@pconfig(constructs=WillBeRunnable)
class WillBeRunnableConfig:
    pass


cfg = WillBeRunnableConfig()
obj: WillBeRunnable = cfg.construct()

# Ensure ConfigRunnable WAS injected
assert isinstance(obj, ConfigRunnable), "@pconfiged(runnable=True) must inject ConfigRunnable when absent"
assert issubclass(type(obj), ConfigRunnable), "Class should inherit ConfigRunnable when runnable=True"

print(f"{path.basename(__file__)}  Runnable=True injection test passed.")
