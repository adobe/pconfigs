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
from os import path

from pconfigs.pinnable import Pin, Pinned, pconfig, pconfiged, pdefaults, pproperty


@pconfiged
class Test:
    config: FirstConfig


@pconfig(constructs=Test)
class FirstConfig:
    x: Pinned[float]
    y: float
    z: Pinned[float]

    @pproperty
    def x(self) -> float:
        return self.y * 2


pdefaults += FirstConfig(
    x=Pinned,
    y=2.0,
    z=Pin(3.0),
)


@pconfig(inherit_constructable_type=True)
class SecondConfig(FirstConfig):
    x: Pinned[int]

    @pproperty
    def x(self) -> int:
        return int(self.y * 20)


pdefaults += SecondConfig(
    y=3.0,
)


@pconfig(inherit_constructable_type=True)
class ThirdConfig(SecondConfig):
    x: Pinned[str]

    @pproperty
    def x(self) -> str:
        return str(self.y * 200)


pdefaults += ThirdConfig(
    y=4.0,
)


first_config = FirstConfig()
second_config = SecondConfig()
third_config = ThirdConfig()

assert isinstance(first_config.x, float)
assert first_config.x == 4.0
assert first_config.y == 2.0
assert first_config.z == 3.0

assert isinstance(second_config.x, int)
assert second_config.x == 60
assert second_config.y == 3.0
assert second_config.z == 3.0

assert isinstance(third_config.x, str)
assert third_config.x == "800.0"
assert third_config.y == 4.0
assert third_config.z == 3.0


def get_stubflag_mro(cls):
    return [getattr(x, "__is_pconfig_stub__", None) for x in cls.mro()]


def collapse_stubflag_runs_in_mro(mro):
    return [g for g, _ in groupby(mro)]


for ConfigType in [FirstConfig, SecondConfig, ThirdConfig]:
    # In the mro of these ConfigType's, we should see __is_pconfig_stub__ property take on values like this:
    #   [False, True, None, None, None]
    # where None occurrs for all clases that were not stubs. Once a stub exists in the MRO, all subsequent classes
    # should be stubbed, and the pattern should expand like this:
    #   [False, False, True, True, None, None, None]
    # where we have a run of False flags first, then a run of True flags, and then a run of None flags. This is the
    # necessary requirement for a config class hierarchy to avoid errors about default values when we create a
    # dataclass from the the class type.

    stub_mro = get_stubflag_mro(ConfigType)
    collapsed_stub_mro = collapse_stubflag_runs_in_mro(stub_mro)

    assert collapsed_stub_mro == [False, True, None]

print(f"{path.basename(__file__)}  Extended stubbing tests passed.")
