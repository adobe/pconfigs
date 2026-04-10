# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from pconfigs.pinnable import pconfig, pconfiged

# Suppose the following class is imported from an external library that we cannot modify.
class KwargedClass:
    def __init__(self, x: float, param_a: float = 1.0, param_b: float = 2.0):
        self.x = x
        self.param_a = param_a
        self.param_b = param_b


@pconfig(mocks=KwargedClass)
class KwargedClassConfig:
    pass


kwarged_class_config = KwargedClassConfig()

print(kwarged_class_config)


@pconfiged(mock=True)
class DerivedClass(KwargedClass):
    config: DerivedClassConfig

    def forward(self):
        print(f"Custom config value: y={self.config.y}")


@pconfig(constructs=DerivedClass)
class DerivedClassConfig:
    y: int


derived_class_config = DerivedClassConfig(
    y=10,
)
derived_class = derived_class_config.construct(x=100)


derived_class.forward()