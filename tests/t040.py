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

from pconfigs import pconfig, pdefaults, psetter


@pconfig
class OtherConfig:
    a: str
    b: str


pdefaults += OtherConfig(
    a="a",
    b="b",
)


@pconfig
class OtherConfig2(OtherConfig):
    c: str
    d: str


pdefaults += OtherConfig2(
    c="c",
    d="d",
)


@pconfig
class TestConfig:
    x: float
    y: float
    other: OtherConfig


pdefaults += TestConfig(
    x=1,
    y=2,
    other=pdefaults(OtherConfig),
)


test_config = TestConfig(
    other=pdefaults(OtherConfig2),
)


#### Test that we can construct with defaults.
ps: TestConfig = psetter(type=TestConfig)
ps.y = 20
ps.other.b = "bb"
config = psetter(construct=ps)


assert config.x == 1
assert config.y == 20
assert config.other.a == "a"
assert config.other.b == "bb"


#### Test that we can construct with another input config, and those values are used instead of the defaults.
other_default = TestConfig(
    x=100,
    y=200,
    other=OtherConfig(
        a="A",
        b="B",
    ),
)

ps: TestConfig = psetter(type=TestConfig, inputs=other_default)
ps.y = 202
ps.other.b = "BB"
config = psetter(construct=ps)


assert config.x == 100
assert config.y == 202
assert config.other.a == "A"
assert config.other.b == "BB"


#### Test that we can use create derived config types, and those will be used instead.
@pconfig
class TestConfig2(TestConfig):
    z: float


pdefaults += TestConfig2(
    z=3,
    other=pdefaults(OtherConfig2),
)


ps: TestConfig = psetter(type=TestConfig, inputs=pdefaults(TestConfig2))
ps.y = 202
ps.other.b = "BB"
config = psetter(construct=ps)

assert isinstance(config, TestConfig2)
assert isinstance(config.other, OtherConfig2)
assert config.x == 1
assert config.y == 202
assert config.z == 3
assert config.other.a == "a"
assert config.other.b == "BB"
assert config.other.c == "c"
assert config.other.d == "d"


#### Test that we get an error when the configs aren't the right types.
trash_config = TestConfig2(
    other=other_default,
)

try:
    ps: TestConfig = psetter(type=TestConfig, inputs=trash_config)
    ps.y = 202
    ps.other.b = "BB"
    config = psetter(construct=ps)
    raise RuntimeError("Expected a ValueError")
except ValueError as e:
    if (
        "Inputs attribute TestConfig.other is of type TestConfig, which doesn't match the expected type OtherConfig."
        not in str(e)
    ):
        raise RuntimeError("Expected a ValueError")

print(f"{path.basename(__file__)}  psetter tests passed.")
