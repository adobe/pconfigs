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

from pconfigs import NoneConfig, pconfig, pconfiged, pdefaults
from pconfigs.constructable import ConfigConstructableInterface


#### Test 1: NoneConfig() is constructible with no args and construct() returns None.
nc = NoneConfig()
assert nc.construct() is None, f"Test 1 failed: expected None, got {nc.construct()!r}"


#### Test 2: NoneConfig is recognized as a ConfigConstructableInterface.
assert isinstance(
    nc, ConfigConstructableInterface
), "Test 2 failed: NoneConfig should be a ConfigConstructableInterface."


#### Test 3: NoneConfig instances compare equal (so autocopy treats them as fungible).
assert NoneConfig() == NoneConfig(), "Test 3 failed: two NoneConfig() instances should compare equal."


#### Test 3b: NoneConfig is a singleton (like None itself: ``NoneConfig() is NoneConfig()``).
assert NoneConfig() is NoneConfig(), "Test 3b failed: NoneConfig() should return the same instance every call."


#### Test 4: NoneConfig rejects unknown kwargs.
try:
    NoneConfig(unknown=1)
    raise AssertionError("Test 4 failed: NoneConfig should reject unknown kwargs.")
except TypeError as e:
    assert "unknown" in str(e), f"Test 4 failed: error should mention 'unknown', got: {e}"


#### Test 5: pdefaults(NoneConfig) returns a default-registered NoneConfig instance.
default_nc = pdefaults(NoneConfig)
assert isinstance(default_nc, NoneConfig), f"Test 5 failed: pdefaults(NoneConfig) returned {type(default_nc).__name__}"
assert default_nc.construct() is None, "Test 5 failed: default-registered NoneConfig should construct to None."


#### Test 6: NoneConfig in a union field replaces the verbose Optional[X] + ternary pattern.
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
    sub_config: SubThingConfig | NoneConfig


# Sub-config is "off"
container_off = ContainerConfig(sub_config=NoneConfig()).construct()
assert container_off.sub is None, f"Test 6 failed (off): sub should be None, got {container_off.sub!r}"

# Sub-config is "on"
container_on = ContainerConfig(sub_config=SubThingConfig(x=4.0)).construct()
assert isinstance(
    container_on.sub, SubThing
), f"Test 6 failed (on): sub should be SubThing, got {type(container_on.sub).__name__}"
assert container_on.sub.value() == 8.0, f"Test 6 failed (on): sub.value()={container_on.sub.value()}"


#### Test 7: Auto-copy preserves the user-set NoneConfig() but allows overriding to a real config.
config_off = ContainerConfig(sub_config=NoneConfig())
config_override = ContainerConfig(config_off, sub_config=SubThingConfig(x=7.0))
container_override = config_override.construct()
assert isinstance(container_override.sub, SubThing), "Test 7 failed: override should produce SubThing."
assert container_override.sub.value() == 14.0, f"Test 7 failed: sub.value()={container_override.sub.value()}"


#### Test 8: Repr of a NoneConfig-valued field is readable.
config_repr = repr(ContainerConfig(sub_config=NoneConfig()))
assert "NoneConfig" in config_repr, f"Test 8 failed: repr should mention NoneConfig. Got:\n{config_repr}"


print(f"{os.path.basename(__file__)}  NoneConfig: all tests passed.")
