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

from pconfigs.environment import EnvironmentBase, EnvironmentMetaclass, EnvVar
from pconfigs.pinnable import penv


@penv(convention="uppercase")
class UpperEnv:
    some_thing: str = "value"
    anotherOne: int = 2


# Metaclass and base
assert isinstance(UpperEnv, EnvironmentMetaclass)
assert issubclass(UpperEnv, EnvironmentBase)

# Verify the underlying EnvVar os_names are uppercased
info_some: EnvVar = UpperEnv.get_info("some_thing")
info_another: EnvVar = UpperEnv.get_info("anotherOne")
assert info_some.os_name == "SOME_THING"
assert info_another.os_name == "ANOTHERONE"

# Defaults
assert UpperEnv.some_thing == "value"
assert UpperEnv.anotherOne == 2

# Overrides via environment use uppercased names
os.environ["SOME_THING"] = "OVERRIDE"
os.environ["ANOTHERONE"] = "7"
assert UpperEnv.some_thing == "OVERRIDE"
assert UpperEnv.anotherOne == 7

print(f"{path.basename(__file__)}  @penv convention=uppercase test passed.")
