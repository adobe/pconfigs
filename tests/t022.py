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

from pconfigs.pinnable import Pin, Pinned, pconfig, pconfiged, pdefaults, pinputs, pproperty


@pconfig
class TestConfig:
    x: float
    y: float
    z: Pinned[float]

    @pproperty
    def x(self) -> float:
        return pinputs(self).x * 2


test_config = TestConfig(
    x=1,
    y=2,
    z=Pin(3),
)

assert test_config.x == 2
assert test_config.y == 2
assert test_config.z == 3


print(f"{path.basename(__file__)}  pinputs tests passed.")
