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

from pconfigs.pinnable import PEnum, penum


@penum
class Thing:
    x = "x"
    y = "y"


# Should behave the same as subclassing PEnum directly
assert issubclass(Thing, PEnum), "@penum should re-base class to inherit from PEnum"
assert Thing.x.value == "x", "Enum member value mismatch for x"
assert Thing.y.value == "y", "Enum member value mismatch for y"

# Ensure representation uses PEnum's __repr__
assert repr(Thing.x).startswith("Thing."), "__repr__ should use enum-style format"

print(f"{path.basename(__file__)}  @penum basic test passed.")


