# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from enum import Enum
from os import path
from typing import Any, Dict, List

from torch import nn

from pconfigs import Pinned, pconfig, pconfiged, pdefaults, penum, penv, pproperty


class JunkEnum(Enum):
    First = "first"
    Second = 2


@penum
class MyEnum:
    First = "first"
    Second = 2


@pconfig
class ThingConfig:
    first: Any
    field: List[Any]
    thing: Dict[str, Any]


thing_config = ThingConfig(
    first=nn.Linear,
    field=[nn.Linear],
    thing={"first": nn.Linear},
)
if "<class" in str(thing_config):
    raise ValueError("Class names should not be printed in the form '<class 'something'>'.")

thing_config = ThingConfig(
    first=nn.Linear,
    field=[nn.Linear, thing_config],
    thing={"first": nn.Linear, "second": thing_config},
)

if "<class" in str(thing_config):
    raise ValueError("Class names should not be printed in the form '<class 'something'>'.")


thing_config = ThingConfig(
    first=repr(JunkEnum.Second),
    field=[repr(JunkEnum.First)],
    thing={"thing": repr(JunkEnum.First)},
)
print(thing_config)

print(repr(MyEnum.First))
print(repr(MyEnum.Second))

print(f"{path.basename(__file__)}  Printing with class names test passed.")
