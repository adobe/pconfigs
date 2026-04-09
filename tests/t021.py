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
from typing import get_type_hints

from pconfigs.pinnable import Pin, Pinned, pconfig, pconfiged, pdefaults, pproperty


@pconfig
class TestConfig:
    x: float
    y: float
    z: Pinned[float]
    w: float

    @pproperty
    def x(self) -> float:
        return self.y * 2


#### Verify that we can construct a config as usual when a default has not been set.
config = TestConfig(
    x=1,
    y=2,
    z=Pin(3),
    w=4,
)
assert config.x == 4
assert config.y == 2
assert config.z == 3
assert config.w == 4

#### Verify that we get an error when we omit a variable and a default has not been set.
try:
    _ = TestConfig(
        y=2,
        z=Pin(3),
        w=4,
    )
    raise AssertionError("Expected TypeError when 'x' is omitted and no default is set")
except TypeError as e:
    assert "missing 1 required positional argument: 'x'" in str(e)


pdefaults += TestConfig(
    x=1,
    y=2,
    z=Pin(3),
    w=4,
)


#### Validate that default is registered on the class
assert hasattr(TestConfig, "default_config")
assert isinstance(TestConfig.default_config, TestConfig)
assert TestConfig.default_config.y == 2
assert TestConfig.default_config.x == 4
assert TestConfig.default_config.z == 3
assert TestConfig.default_config.w == 4

#### Callable access on pdefaults returns the default instance
assert pdefaults(TestConfig) is TestConfig.default_config
assert pdefaults(TestConfig.default_config) is TestConfig.default_config
try:
    _ = pdefaults(123)  # type: ignore[arg-type]
    raise AssertionError("Expected TypeError for invalid pdefaults(...) input")
except TypeError:
    pass

#### Confirm that registering a second default for the same type throws an error
try:
    pdefaults += TestConfig(
        x=9,
        y=9,
        z=Pin(9),
        w=9,
    )
    raise AssertionError("Expected ValueError when setting two defaults for the same config type")
except ValueError as e:
    assert "already set" in str(e)


#### Construct with only y overridden. Verify that the other parameters come from the set defaults.
test_config = TestConfig(
    y=10,
)
assert test_config.y == 10  # explicit
assert test_config.x == 20  # computed from y
assert test_config.z == 3  # from defaults (unpinned value via Pin)
assert test_config.w == 4  # from defaults


#### Verify that we can create a default for a derived class by using the parent's defaults.
#### After this operation, the default config type should be updated to an instance of ChildTestConfig,
#### and it should not be possible to set defaults anymore.
@pconfig
class ChildTestConfig(TestConfig):
    q: float


pdefaults += ChildTestConfig(
    q=9,
)

#### Verify that the default config type is updated to an instance of ChildTestConfig
assert isinstance(ChildTestConfig.default_config, ChildTestConfig)
assert ChildTestConfig.default_config.q == 9
assert pdefaults(ChildTestConfig) is ChildTestConfig.default_config

#### Verify that it is not possible to set defaults anymore
try:
    pdefaults += ChildTestConfig(
        q=10,
    )
    raise AssertionError("Expected ValueError when setting defaults for a derived class")
except ValueError as e:
    assert "already set" in str(e)

#### Verify that we can construct a child config instance using the default config
child_test_config = ChildTestConfig(
    y=6,
)
assert child_test_config.y == 6
assert child_test_config.x == 12
assert child_test_config.z == 3
assert child_test_config.w == 4
assert child_test_config.q == 9


#### Calling pdefaults on a config with no default returns None
@pconfig
class FreshConfig:
    a: float


assert pdefaults(FreshConfig) is None


print(f"{path.basename(__file__)}  @pdefaults tests passed.")
