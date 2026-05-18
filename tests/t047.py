# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

import os
from typing import Union, get_type_hints

from pconfigs import NoneConfig, OptionalConfig, pconfig, pconfiged, pdefaults
from pconfigs.constructable import ConfigConstructableInterface


#### Test 1: NoneConfig is a value (not a class) and NoneConfig.construct() returns None.
assert NoneConfig.construct() is None, f"Test 1 failed: expected None, got {NoneConfig.construct()!r}"


#### Test 2: NoneConfig is an instance of OptionalConfig and of ConfigConstructableInterface.
assert isinstance(NoneConfig, OptionalConfig), "Test 2 failed: NoneConfig should be an OptionalConfig instance."
assert isinstance(
    NoneConfig, ConfigConstructableInterface
), "Test 2 failed: NoneConfig should be a ConfigConstructableInterface."


#### Test 3: OptionalConfig() returns the NoneConfig singleton (mirrors NoneType() is None... almost).
assert OptionalConfig() is NoneConfig, "Test 3 failed: OptionalConfig() should return the NoneConfig singleton."
assert OptionalConfig() is OptionalConfig(), "Test 3 failed: OptionalConfig() must be a singleton."


#### Test 4: OptionalConfig rejects unknown kwargs.
try:
    OptionalConfig(unknown=1)
    raise AssertionError("Test 4 failed: OptionalConfig should reject unknown kwargs.")
except TypeError as e:
    assert "unknown" in str(e), f"Test 4 failed: error should mention 'unknown', got: {e}"


#### Test 5: pdefaults(OptionalConfig) returns the NoneConfig singleton.
default_nc = pdefaults(OptionalConfig)
assert default_nc is NoneConfig, "Test 5 failed: pdefaults(OptionalConfig) should return NoneConfig."
assert default_nc.construct() is None, "Test 5 failed: default-registered OptionalConfig should construct to None."


#### Test 6: OptionalConfig[T] subscript resolves to Union[T, OptionalConfig].
class _Probe:
    pass


assert OptionalConfig[_Probe] == Union[_Probe, OptionalConfig], (
    f"Test 6 failed: OptionalConfig[T] should be Union[T, OptionalConfig], "
    f"got {OptionalConfig[_Probe]!r}"
)


#### Test 7: OptionalConfig[T] in a field annotation replaces the verbose Optional[X] + ternary pattern.
@pconfiged
class SubThing:
    config: SubThingConfig

    def __init__(self):
        pass

    def value(self) -> float:
        return self.config.x * 2


@pconfig(constructs=SubThing)
class SubThingConfig:
    x: float


@pconfiged
class Container:
    config: ContainerConfig

    def __init__(self):
        self.sub = self.config.sub_config.construct()


@pconfig(constructs=Container)
class ContainerConfig:
    sub_config: OptionalConfig[SubThingConfig]


# Confirm the subscripted annotation resolves to Union[SubThingConfig, OptionalConfig] at the class level.
hints = get_type_hints(ContainerConfig)
assert hints["sub_config"] == Union[SubThingConfig, OptionalConfig], (
    f"Test 7 failed: ContainerConfig.sub_config should resolve to Union[SubThingConfig, OptionalConfig], "
    f"got {hints['sub_config']!r}"
)

# Sub-config is "off"
container_off = ContainerConfig(sub_config=NoneConfig).construct()
assert container_off.sub is None, f"Test 7 failed (off): sub should be None, got {container_off.sub!r}"

# Sub-config is "on"
container_on = ContainerConfig(sub_config=SubThingConfig(x=4.0)).construct()
assert isinstance(
    container_on.sub, SubThing
), f"Test 7 failed (on): sub should be SubThing, got {type(container_on.sub).__name__}"
assert container_on.sub.value() == 8.0, f"Test 7 failed (on): sub.value()={container_on.sub.value()}"


#### Test 8: Bare ``T | OptionalConfig`` union annotation also works.
@pconfiged
class OtherContainer:
    config: OtherContainerConfig

    def __init__(self):
        self.sub = self.config.sub_config.construct()


@pconfig(constructs=OtherContainer)
class OtherContainerConfig:
    sub_config: SubThingConfig | OptionalConfig


other_off = OtherContainerConfig(sub_config=NoneConfig).construct()
assert other_off.sub is None, f"Test 8 failed (off): sub should be None, got {other_off.sub!r}"

other_on = OtherContainerConfig(sub_config=SubThingConfig(x=3.0)).construct()
assert other_on.sub.value() == 6.0, f"Test 8 failed (on): sub.value()={other_on.sub.value()}"


#### Test 9: Auto-copy preserves the user-set NoneConfig but allows overriding to a real config.
config_off = ContainerConfig(sub_config=NoneConfig)
config_override = ContainerConfig(config_off, sub_config=SubThingConfig(x=7.0))
container_override = config_override.construct()
assert isinstance(container_override.sub, SubThing), "Test 9 failed: override should produce SubThing."
assert container_override.sub.value() == 14.0, f"Test 9 failed: sub.value()={container_override.sub.value()}"


#### Test 10: Repr of an OptionalConfig-valued field is readable.
config_repr = repr(ContainerConfig(sub_config=NoneConfig))
assert "OptionalConfig" in config_repr, f"Test 10 failed: repr should mention OptionalConfig. Got:\n{config_repr}"


print(f"{os.path.basename(__file__)}  OptionalConfig / NoneConfig: all tests passed.")
