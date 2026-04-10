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


@penv
class MyEnv:
    thing: str = EnvVar("TEST_THING", "default_value")
    number: int = EnvVar("TEST_NUMBER", 3)
    flag: bool = EnvVar("TEST_FLAG", 0)


# Defaults apply when variables are unset
assert MyEnv.thing == "default_value"
assert MyEnv.number == 3
assert MyEnv.flag is False

# Setting environment variables should reflect in the class values
os.environ["TEST_THING"] = "hello"
os.environ["TEST_NUMBER"] = "7"
os.environ["TEST_FLAG"] = "1"

assert MyEnv.thing == "hello"
assert MyEnv.number == 7
assert MyEnv.flag is True

# Class should be using the EnvironmentMetaclass and derive from EnvironmentBase
assert isinstance(MyEnv, EnvironmentMetaclass)
assert issubclass(MyEnv, EnvironmentBase)

print(f"{path.basename(__file__)}  @penv basic test passed.")


