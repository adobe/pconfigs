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

from pconfigs.environment import EnvironmentBase, EnvironmentMetaclass, EnvVar
from pconfigs.pinnable import penv


class AlreadyEnv(metaclass=EnvironmentMetaclass):
    thing: str = EnvVar("TEST_THING2", "value2")


AlreadyEnv2 = penv(AlreadyEnv)

# Rebuild allowed: verify metaclass and behavior remain correct
assert isinstance(AlreadyEnv2, EnvironmentMetaclass)
assert issubclass(AlreadyEnv2, EnvironmentBase)
assert AlreadyEnv2.thing == "value2"

print(f"{path.basename(__file__)}  @penv no-op test passed.")


