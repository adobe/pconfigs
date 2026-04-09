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

from pconfigs.pinnable import Pin, Pinned, Required, pconfig, pconfiged, pdefaults, pinputs, pproperty


class KwargedClass:
    def __init__(self, x: float, param_a: float = 1.0, param_b: float = 2.0):
        self.x = x
        self.param_a = param_a
        self.param_b = param_b

    def __str__(self):
        config_str = "\n".join(f"  {line}" for line in str(self.config).split("\n"))
        return f"{type(self).__name__}(\n  x={self.x},\n  config={config_str.strip()},\n)"


@pconfig(mocks=KwargedClass)
class KwargedClassConfig:
    pass


kwarged_class = KwargedClassConfig().construct(x=100)


@pconfiged(mock=True)
class DerivedClass(KwargedClass):
    config: DerivedClassConfig

    def __str__(self):
        parent_str = super().__str__()
        return f"{parent_str}\n  y={self.config.y},\n)"
 

@pconfig(constructs=DerivedClass)
class DerivedClassConfig:
    y: int


derived_class_config = DerivedClassConfig(
    y=10,
)
derived_class = derived_class_config.construct(x=100)

print(f"{path.basename(__file__)}  @pconfiged(mock=True) tests passed.")
