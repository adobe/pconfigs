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
    x: float
    y: float


pdefaults += FirstConfig(
    x=1.0,
    y=2.0,
)


@pconfig(inherit_constructable_type=True)
class SecondConfig(FirstConfig):
    z: Pinned[float]

    @pproperty
    def z(self) -> float:
        return self.x + self.y


pdefaults += SecondConfig(
    z=Pinned,
)


# This created a problem at first. There was an issue with how the __init__ process worked once stubbing was implemented
# correctly. The pconfig wrapper __init__ must call the __init__ that is defined by the dataclass of the most derived
# stub class in the mro.
@pconfig(inherit_constructable_type=True)
class ThirdConfig(SecondConfig):
    q: float


pdefaults += ThirdConfig(
    q=4.0,
)


@pconfig(inherit_constructable_type=True)
class FourthConfig(ThirdConfig):
    r: float

    @pproperty
    def z(self) -> float:
        return self.r + self.x + self.y


pdefaults += FourthConfig(
    r=5.0,
)

first_config = FirstConfig()
second_config = SecondConfig()
third_config = ThirdConfig()
fourth_config = FourthConfig()

assert first_config.x == 1.0
assert first_config.y == 2.0

assert second_config.x == 1.0
assert second_config.y == 2.0
assert second_config.z == 3.0

assert third_config.x == 1.0
assert third_config.y == 2.0
assert third_config.z == 3.0
assert third_config.q == 4.0

assert fourth_config.x == 1.0
assert fourth_config.y == 2.0
assert fourth_config.z == 8.0
assert fourth_config.q == 4.0
assert fourth_config.r == 5.0


def get_stubflag_mro(cls):
    return [getattr(x, "__is_pconfig_stub__", None) for x in cls.mro()]


def collapse_stubflag_runs_in_mro(mro):
    return [g for g, _ in groupby(mro)]


def stubflag_mro_is_ok(ConfigType):
    stub_mro = get_stubflag_mro(ConfigType)
    stub_mro_collapsed = collapse_stubflag_runs_in_mro(stub_mro)

    ok_patterns = (
        [False, True, None],
        [None],
    )

    return stub_mro_collapsed in ok_patterns


for ConfigType in [FirstConfig, SecondConfig, ThirdConfig]:
    assert stubflag_mro_is_ok(ConfigType)


# Make sure we didn't break the top-level construction process somehow.
first = first_config.construct()
second = second_config.construct()
third = third_config.construct()
fourth = fourth_config.construct()

print(f"{path.basename(__file__)}  Extended stubbing constructor tests passed.")
