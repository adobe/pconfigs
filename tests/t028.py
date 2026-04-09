# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from itertools import groupby
from math import e
from os import path

from pconfigs.pinnable import Pin, Pinned, pconfig, pconfiged, pdefaults, pinputs, pproperty


@pconfig
class BaseConfig:
    x: float


try:

    @pconfig
    class FirstConfig(BaseConfig):
        y: float

        @pproperty
        def x(self) -> float:
            return self.y + 1

        @pproperty
        def y(self) -> float:
            return self.x + 1

    raise ValueError("Expected ValueError that detects a circular property dependency.")

except ValueError as e:
    if "FirstConfig has circular property dependencies" not in str(e):
        raise e


#### Test a case when our auto-detected dependencies are not sufficient to detect a circular property dependency.
#### The user should be able to augment the dependencies in that case.
try:

    @pconfig
    class SecondConfig(BaseConfig):
        y: float

        @pproperty(deps="y")
        def x(self) -> float:
            prop_name = "y"
            return getattr(self, prop_name) + 1

        @pproperty
        def y(self) -> float:
            return self.x + 1

    raise ValueError("Expected ValueError that detects a circular property dependency.")

except ValueError as e:
    if "SecondConfig has circular property dependencies" not in str(e):
        raise e


print(f"{path.basename(__file__)}  Circular property dependency check passed.")
