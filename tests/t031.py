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

from PIL import ImageFont

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
#     thing: Pinned[str]
#     other: str
#     value: float
# 
#     @pproperty
#     def thing(self) -> str:
#         return self.other * 3
# 
# 
# default_third_config = ThirdConfig(
#     thing=Pinned,
#     other="2",
#     value=3.0,
# )
# 
# assert default_third_config.thing == "222"
# assert default_third_config.other == "2"
# assert default_third_config.value == 3.0


print(f"{path.basename(__file__)}  @pconfig builds config when base configs are stubbed in a legacy manner.")
