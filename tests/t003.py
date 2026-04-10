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

from pconfigs.pinnable import pconfig, pconfiged, pproperty


@pconfiged
class Test:
    config: TestConfig


@pconfig(constructs=Test)
class TestConfig:
    x: float
    y: float

    @pproperty
    def x(self) -> float:
        return self.y * 2


@pconfiged
class Derived(Test):
    config: DerivedConfig


@pconfig(constructs=Derived)
class DerivedConfig(TestConfig):
    z: float


test_config = TestConfig(x=1, y=2)
derived_config = DerivedConfig(
    test_config,
    z=3,
)

derived: Derived = derived_config.construct()
# print(derived)
# print(derived.config)


# Test pickling and unpickling the derived config
import os
import pickle
import tempfile

tmp_path = None
with tempfile.NamedTemporaryFile(delete=False) as f:
    tmp_path = f.name
    pickle.dump(derived_config, f)

with open(tmp_path, "rb") as f:
    loaded_cfg: DerivedConfig = pickle.load(f)

os.unlink(tmp_path)

# Validate fields and behavior after unpickle
assert isinstance(loaded_cfg, DerivedConfig)
assert loaded_cfg.z == 3
assert loaded_cfg.y == 2
assert loaded_cfg.x == 4  # computed property still works

loaded_obj: Derived = loaded_cfg.construct()
assert isinstance(loaded_obj, Derived)
assert isinstance(loaded_obj.config, DerivedConfig)

print(f"{path.basename(__file__)}  Pickling tests passed.")
