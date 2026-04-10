# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from pconfigs import pconfig, pdefaults, psetter


@pconfig
class SubConfig:
    a: int
    b: int


pdefaults += SubConfig(
    a=10,
    b=20,
)

@pconfig
class TestConfig:
    x: int
    y: int
    config: SubConfig


pdefaults += TestConfig(
    x=1,
    y=2,
    config=pdefaults(SubConfig),
)


test_config: TestConfig = psetter(type=TestConfig)
test_config.x = 1
test_config.config.a = 2
test_config = psetter(construct=test_config)


print(test_config)

