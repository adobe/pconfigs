# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from itertools import groupby
from os import path

from pconfigs.pinnable import Pin, Pinned, pconfig, pconfiged, pdefaults, pinputs, pproperty


@pconfig
class FirstConfig:
    x: Pinned[float]
    y: float

    @pproperty
    def y(self) -> float:
        if self.x is Pinned:
            raise ValueError("x is pinned")

        return self.x + pinputs(self).y


first_config = FirstConfig(
    x=Pinned,
    y=1.0,
)

assert first_config.x is Pinned
assert first_config.y is Pinned


# Removing this test because we don't support legacy mode anymore
# TBD if it should be here for some reason, but modified somehow.
# @pconfig
# class SecondConfig:
#     x: Pinned[float]
#     y: float
# 
#     @pproperty(legacy_mode=True)
#     def y(self) -> float:
#         if self.x is Pinned:
#             raise ValueError("x is pinned")
# 
#         return self.x + pinputs(self).y
# 
# 
# try:
#     second_config = SecondConfig(
#         x=Pinned,
#         y=1.0,
#     )
#     raise ValueError("Expected ValueError")
# except ValueError as e:
#     if "x is pinned" not in str(e):
#         raise e

print(f"{path.basename(__file__)}  @pproperty dependency analysis tests passed.")
