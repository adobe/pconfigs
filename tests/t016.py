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
from os import path

from pconfigs.environment import EnvironmentBase, EnvironmentMetaclass
from pconfigs.pinnable import penv


@penv
class BaseEnv:
    thing: str = "base"
    count: int = 1


@penv
class DerivedEnv(BaseEnv):
    # Override existing env var with new default
    thing: str = "derived"
    # Add a new env var
    flag: bool = 0


# Metaclass applied
assert isinstance(BaseEnv, EnvironmentMetaclass)
assert isinstance(DerivedEnv, EnvironmentMetaclass)
assert issubclass(BaseEnv, EnvironmentBase)
assert issubclass(DerivedEnv, EnvironmentBase)

# Defaults
assert BaseEnv.thing == "base"
assert BaseEnv.count == 1
assert DerivedEnv.thing == "derived"
assert DerivedEnv.count == 1
assert DerivedEnv.flag is False

# Environment overrides only affect the class where read is performed
os.environ["thing"] = "override"
os.environ["count"] = "9"
os.environ["flag"] = "1"

assert BaseEnv.thing == "override"  # reads from env
assert BaseEnv.count == 9
assert DerivedEnv.thing == "override"  # reads same env var name
assert DerivedEnv.count == 9
assert DerivedEnv.flag is True

print(f"{path.basename(__file__)}  Derived env override/add test passed.")


