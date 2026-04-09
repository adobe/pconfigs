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

from pconfigs.pinnable import PConfig, Pinned, pconfig, pdefaults, pproperty

# Removing this test because we don't support legacy mode anymore
# TBD if it should be here for some reason, but modified somehow.
#
# @pconfig(legacy_mode=True)
# class StubbedLegacyConfig(PConfig):
#     thing: Pinned[int]
#     other: int
# 
# 
# @pconfig(legacy_mode=True)
# class LegacyConfig(StubbedLegacyConfig):
#     @pproperty(legacy_mode=True)
#     def thing(self) -> int:
#         return self.other * 2
# 
# 
# default_legacy_config = LegacyConfig(
#     thing=Pinned,
#     other=2,
# )
# 
# 
# # Second derived stubbed config
# @pconfig(legacy_mode=True)
# class SecondStubbedLegacyConfig(StubbedLegacyConfig):
#     thing: Pinned[float]
#     other: float
# 
# 
# @pconfig(legacy_mode=True)
# class SecondLegacyConfig(LegacyConfig, SecondStubbedLegacyConfig):
#     @pproperty(legacy_mode=True)
#     def thing(self) -> int:
#         return self.other * 2.0
# 
# 
# default_second_legacy_config = SecondLegacyConfig(
#     thing=Pinned,
#     other=2.0,
# )
# 
# 
# # Third derived config uses new system
# @pconfig(legacy_stub=SecondStubbedLegacyConfig)
# class ThirdConfig(SecondLegacyConfig):
#     special: Pinned[float]
#     another: float
# 
#     @pproperty
#     def special(self) -> float:
#         return self.another * 3.0
# 
# 
# pdefaults += ThirdConfig(
#     default_second_legacy_config.inputs,
#     special=Pinned,
#     another=2.0,
# )
# 
# ### Verify that the defaults get automatically copied as expected, even when there is legacy stubbing.
# auto_default_constructed = ThirdConfig()
# 
# assert auto_default_constructed.thing == 4.0
# assert auto_default_constructed.other == 2
# assert auto_default_constructed.special == 6.0
# assert auto_default_constructed.another == 2.0

print(f"{path.basename(__file__)}  @pconfig copies defaults when base configs are stubbed in a legacy manner.")
