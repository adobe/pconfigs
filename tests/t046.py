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

from pconfigs import PCallable, pconfig, pdefaults


#### Test 1: pdefaults for a standalone @pconfig(calls=func) returns a callable instance.
def standalone_func(x: float, scale: float = 1.0, offset: float = 0.0) -> float:
    return x * scale + offset


@pconfig(calls=standalone_func)
class StandaloneFunc:
    pass


standalone_default = pdefaults(StandaloneFunc)
assert isinstance(standalone_default, StandaloneFunc)
assert isinstance(standalone_default, PCallable)
assert standalone_default.scale == 1.0
assert standalone_default(x=5.0) == 5.0


#### Test 2: @pconfig(calls=func) forbids inheriting from any base class.
def parent_func(batch: list) -> list:
    return batch


def child_func(batch: list) -> list:
    return [item * 2 for item in batch]


@pconfig(calls=parent_func)
class ParentFunc:
    pass


try:

    @pconfig(calls=child_func)
    class ChildFunc(ParentFunc):
        pass

    raise AssertionError("Test 2 failed: expected TypeError for @pconfig(calls=...) inheritance.")
except TypeError as e:
    assert "must not inherit from" in str(e), f"Test 2 failed: unexpected TypeError message: {e}"


print(f"{os.path.basename(__file__)}  @pconfig(calls=...): all tests passed.")
