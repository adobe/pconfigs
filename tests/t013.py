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


class AlreadyEnum(PEnum):
    a = "a"
    b = "b"


# Applying @penum should be a no-op for classes already subclassing PEnum
AlreadyEnum2 = penum(AlreadyEnum)

assert AlreadyEnum2 is AlreadyEnum, "@penum should be a no-op if class already subclasses PEnum"
assert AlreadyEnum2.a.value == "a"
assert AlreadyEnum2.b.value == "b"

print(f"{path.basename(__file__)}  @penum no-op test passed.")


