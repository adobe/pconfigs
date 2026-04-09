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

from pconfigs.pinnable import Pinned, pconfig, pconfiged, pproperty

"""
Test that user can call super().__init__() without passing the config parameter.
"""


#### 1. Empty configs don't break anything.
#### 2. Constructed type matches the @pconfig(constructs=Type)
@pconfiged
class Empty:
    config: EmptyConfig


@pconfig(constructs=Empty)
class EmptyConfig:
    pass


empty = EmptyConfig().construct()
assert isinstance(empty, Empty)


#### 1. pconfig works without a constructable type
@pconfig
class RandomConfig:
    x: float
    y: float


random_config = RandomConfig(x=1, y=2)


#### Config class stubbing works.
@pconfiged
class Test:
    config: TestConfig

    def __init__(self):
        pass

    def myfunc(self):
        return self.config.y


@pconfig(constructs=Test)
class TestConfig:
    x: float
    y: float

    @pproperty
    def x(self) -> float:
        return self.y * 2


test: Test = TestConfig(x=1, y=2).construct()
assert test.config.x == 4
assert test.config.y == 2


#### Super calls work without passing the config parameter.
@pconfiged
class Derived(Test):
    config: DerivedConfig

    def __init__(self):
        super().__init__()


@pconfig(constructs=Derived)
class DerivedConfig(TestConfig):
    z: float


derived: Derived = DerivedConfig(x=1, y=2, z=3).construct()
assert derived.config.x == 4
assert derived.config.y == 2
assert derived.config.z == 3

#### Not allowed to specify parameters in the constructor.
try:

    @pconfiged
    class SecondDerived(Derived):
        config: SecondDerivedConfig

        def __init__(self, param: int):
            super().__init__()

    @pconfig(constructs=Derived)
    class SecondDerivedConfig(DerivedConfig):
        p: float

except TypeError as e:
    if "shall not declare parameters" not in str(e):
        raise


def instantiation_test():
    derived_config = DerivedConfig(x=1, y=2, z=3)
    derived: Derived = derived_config.construct()
    assert derived_config.x == 4
    assert derived_config.y == 2
    assert derived_config.z == 3


instantiation_test()


#### Make sure that we can multiply inherit without encountering stubbing issues.
@pconfig(inherit_constructable_type=False)
class FurtherDerivedConfig(DerivedConfig):
    z: Pinned[float]
    scale: float
    bias: float

    @pproperty
    def z(self) -> float:
        # Compute z from existing y and new fields
        return self.y * self.scale + self.bias


def further_instantiation_test():
    cfg = FurtherDerivedConfig(
        x=1,
        y=2,
        z=Pinned,
        scale=3,
        bias=1,
    )
    # Verify computed and raw values on the config itself
    assert cfg.x == 4  # from TestConfig.pproperty
    assert cfg.y == 2
    assert cfg.scale == 3
    assert cfg.bias == 1
    assert cfg.z == 7  # 2*3 + 1
    try:
        _ = cfg.construct()
        raise AssertionError("Expected TypeError when constructing config with no constructable_type")
    except TypeError as e:
        assert "has no constructable_type bound" in str(e)


further_instantiation_test()


print(f"{path.basename(__file__)}  pconfiged constructor injection tests passed.")
