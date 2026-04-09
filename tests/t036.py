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

from pconfigs.pinnable import Pin, Pinned, pconfig, pconfiged, pdefaults, pproperty


@pconfiged
class First:
    config: FirstConfig

    def __init__(self):
        super().__init__()
        self.value = 1


@pconfig(constructs=First)
class FirstConfig:
    pass


pdefaults += FirstConfig()

first: First = pdefaults(FirstConfig).construct()
assert hasattr(first, "value") and first.value == 1


@pconfiged
class Second(First):
    config: SecondConfig


@pconfig(constructs=Second)
class SecondConfig(FirstConfig):
    pass


pdefaults += SecondConfig()


second: Second = pdefaults(SecondConfig).construct()
assert hasattr(second, "value") and second.value == 1


@pconfiged
class Third(Second):
    config: ThirdConfig

    def __init__(self):
        super().__init__()
        self.other = 2


@pconfig(constructs=Third)
class ThirdConfig(SecondConfig):
    pass


pdefaults += ThirdConfig()


third: Third = pdefaults(ThirdConfig).construct()
assert hasattr(third, "value") and third.value == 1
assert hasattr(third, "other") and third.other == 2


print(f"{path.basename(__file__)}  Basic tests passed.")
