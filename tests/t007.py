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
from typing import ClassVar

from pconfigs.pinnable import Pin, Pinned, pconfig, pconfiged, pproperty


@pconfiged
class Test:
    config: TestConfig

    def __init__(self):
        super().__init__()


@pconfig(constructs=Test)
class TestConfig:
    a: ClassVar[int] = 1
    x: float
    y: float


test_config = TestConfig(
    x=1,
    y=2,
)

test: Test = test_config.construct()

print(f"{path.basename(__file__)}  ClassVar default values are ok - tests passed.")
