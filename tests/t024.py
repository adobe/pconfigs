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


def kwarged_func(x: float, param_a: float = 1.0, param_b: float = 2.0) -> float:
    return x * param_a + param_b


@pconfig(calls=kwarged_func)
class KwargedFuncConfig:
    pass


kwarged_func = KwargedFuncConfig(
    param_a=2.0,
)

result = kwarged_func(x=100)

assert result == 202.0

print(f"{path.basename(__file__)}  @pconfig(calls=True) for functions: tests passed.")
