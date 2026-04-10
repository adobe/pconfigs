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

from pconfigs.pinnable import Pin, Pinned, pconfig, pconfiged, pproperty


@pconfiged
class Test:
    config: TestConfig


@pconfig(constructs=Test)
class TestConfig:
    x: float
    y: float
    z: Pinned[float]

    @pproperty
    def x(self) -> float:
        return self.y * 2


test_config = TestConfig(
    x=1,
    y=2,
    z=Pin(3),
)

test_config2 = TestConfig(
    test_config,
)

try:
    test_config3 = TestConfig(
        x=1,
        y=2,
        z=3,
    )
    raise Exception("A pinned field was set, but an exception was not raised.")
except Exception as e:
    if "cannot set a pinned field" not in str(e).lower():
        raise e


print(f"{path.basename(__file__)}  Pinned field tests passed.")
