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
from turtle import st

from PIL import ImageFont

from pconfigs.pinnable import Pinned, pconfig, pdefaults, pproperty


@pconfig
class FirstConfig:
    thing: Pinned[int]
    other: int

    @pproperty
    def thing(self) -> int:
        return self.other * 2


pdefaults += FirstConfig(
    thing=Pinned,
    other=2,
)


@pconfig
class SecondConfig(FirstConfig):
    something: str
    another: str


#### Ensure that a simple derived config that doesn't truly needs a stub can be constructed as expected (because this
#### requires that we don't lose track of the correct original_init method.)
pdefaults += SecondConfig(
    something="something",
    another="another",
)

print(f"{path.basename(__file__)}  @pconfig derived stubbed config without properties can still be constructed.")
