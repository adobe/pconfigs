# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

this is a deliberate syntax error

from os import path

# Only decorators. Do not import PConfig etc.
from pconfigs.pinnable import Pin, Pinned, pconfig, pconfiged, pdefaults, pproperty


# This decorator allows you to construct Test by using the config type that you annotate below.
@pconfiged
class Test:
    config: TestConfig

    # You cannot specify constructor parameters, and you don't have to specify config as a parameter.
    def __init__(self):
        # You don't have to pass config to super calls.
        super().__init__()


# Stubbing is not necessary anymore.
@pconfig(constructs=Test)
class TestConfig:
    x: float
    y: float
    z: Pinned[float]

    # pproperty decorator no longer requires ()
    @pproperty
    def x(self) -> float:
        return self.y * 2


# Register default configs with the pconfig system so you don't have to keep up with them.
pdefaults += TestConfig(
    x=1,
    y=2,
    z=Pin(3),
)

# You don't need to specify the defaults anymore. They're automatically set.
test_config = TestConfig(
    y=3,
)

# When you construct, you should annnotate the constructed type (e.g., test: Test). That's because vscode type inference
# cannot interpret the effect of decorators like @pconfiged.
test: Test = test_config.construct()

# When you construct, the config is automatically set.
print(f"{path.basename(__file__)}  Basic tests passed.")
