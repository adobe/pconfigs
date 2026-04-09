# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from dataclasses import fields
from os import path
from typing import ClassVar, Type, get_args, get_origin, get_type_hints

from pconfigs.environment import EnvironmentBase, EnvironmentMetaclass
from pconfigs.pinnable import pconfig, pconfiged, penv


@pconfiged
class MyThing:
    config: MyThingConfig


@penv
class MyThingEnvironment:
    value: int = 3


@pconfig(constructs=MyThing)
class MyThingConfig:
    environment: MyThingEnvironment


# Dataclass should not treat 'environment' as a field
field_names = {f.name for f in fields(MyThingConfig)}
assert "environment" not in field_names

# Default value should be the environment class
assert MyThingConfig.environment is MyThingEnvironment
assert isinstance(MyThingEnvironment, EnvironmentMetaclass)
assert issubclass(MyThingEnvironment, EnvironmentBase)

# Type hint must be exactly ClassVar[Type[MyThingEnvironment]] when resolved with extras
annots = get_type_hints(MyThingConfig, include_extras=True)
env_annot = annots["environment"]
outer_origin = get_origin(env_annot)
outer_args = get_args(env_annot)
assert outer_origin is ClassVar and len(outer_args) == 1
inner = outer_args[0]
inner_origin = get_origin(inner)
inner_args = get_args(inner)
assert inner_origin in (Type, type) and len(inner_args) == 1 and inner_args[0] is MyThingEnvironment

print(f"{path.basename(__file__)}  @pconfig(constructs=MyThing) environment annotation normalization test passed.")
