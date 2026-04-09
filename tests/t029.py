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
    y: Pinned[float]

    @pproperty
    def y(self) -> float:
        return self.x * 2


@pconfiged
class Derived:
    config: DerivedConfig


@pconfig(constructs=Derived)
class DerivedConfig(BaseConfig):
    z: float


@pconfig(inherit_constructable_type=True)
class ThirdConfig(DerivedConfig):
    q: float


assert not ("constructable_type" in BaseConfig.__dataclass_fields__.keys())
assert "constructable_type" in DerivedConfig.__dataclass_fields__.keys()
assert "constructable_type" in ThirdConfig.__dataclass_fields__.keys()


assert issubclass(DerivedConfig, BaseConfig)
assert issubclass(ThirdConfig, DerivedConfig)

base_config = BaseConfig(
    x=1,
    y=Pinned,
)
derived_config = DerivedConfig(
    x=1,
    y=Pinned,
    z=3,
)
third_config = ThirdConfig(
    x=1,
    y=Pinned,
    z=3,
    q=4,
)

assert not ("constructable_type" in str(base_config))
assert "constructable_type" in str(derived_config)
assert "constructable_type" in str(third_config)

print(f"{path.basename(__file__)}  Dataclass fields have constructable type.")
