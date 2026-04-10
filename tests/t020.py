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

from pconfigs.pinnable import pconfig


class NotAnEnvironment:
    pass


# Expectation: since 'environment' is reserved and not an EnvironmentBase subclass, @pconfig should raise ValueError
error_raised = False
try:

    @pconfig
    class BadConfig:
        environment: NotAnEnvironment

except ValueError as e:
    error_raised = True
    msg = str(e)
    assert "EnvironmentBase" in msg or "reserved name" in msg

assert error_raised, "@pconfig should raise ValueError for non-EnvironmentBase 'environment' annotation"

print(f"{path.basename(__file__)}  Non-EnvironmentBase 'environment' annotation error test passed.")
