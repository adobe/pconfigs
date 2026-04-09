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

from pconfigs.pinnable import pconfig, pconfiged


@pconfiged
class Test:
    config: TestConfig


try:
    test = Test()
    raise RuntimeError("Test class was constructed without a config argument, but no exception was raised.")
except Exception as e:
    if "class 'Test' must be constructed with a 'config' argument" not in str(e):
        raise e


@pconfig(constructs=Test)
class TestConfig:
    x: float
    y: float


base_config = TestConfig(
    x=1,
    y=2,
)


print(f"{path.basename(__file__)}  Config definition ordering tests passed.")
