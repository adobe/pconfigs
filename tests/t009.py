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


@pconfiged(runnable=False)
class NotRunnable:
    config: NotRunnableConfig


@pconfig(constructs=NotRunnable)
class NotRunnableConfig:
    pass


cfg = NotRunnableConfig()
obj: NotRunnable = cfg.construct()

# Ensure ConfigRunnable was NOT injected
assert not isinstance(obj, ConfigRunnable), "@pconfiged(runnable=False) must not inject ConfigRunnable"
# And class does not become subclass of ConfigRunnable
assert not issubclass(type(obj), ConfigRunnable), "Class should not inherit ConfigRunnable when runnable=False"

print(f"{path.basename(__file__)}  Runnable=False test passed.")
