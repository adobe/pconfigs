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
from pconfigs.pinnable import pconfig, penv


@penv
class MyEnvironment:
    something: str = "value"


@pconfig
class MyConfig:
    environment: MyEnvironment


# Dataclass should not treat 'environment' as a field
field_names = {f.name for f in fields(MyConfig)}
assert "environment" not in field_names

# Default value should be the MyEnvironment class, and class should have metaclass and base set by @penv
assert MyConfig.environment is MyEnvironment
assert isinstance(MyEnvironment, EnvironmentMetaclass)
assert issubclass(MyEnvironment, EnvironmentBase)

# Type hint must be exactly ClassVar[Type[MyEnvironment]] when resolved with extras
annots = get_type_hints(MyConfig, include_extras=True)
assert "environment" in annots
env_annot = annots["environment"]
outer_origin = get_origin(env_annot)
outer_args = get_args(env_annot)
assert outer_origin is ClassVar and len(outer_args) == 1
inner = outer_args[0]
inner_origin = get_origin(inner)
inner_args = get_args(inner)
assert inner_origin in (Type, type) and len(inner_args) == 1 and inner_args[0] is MyEnvironment

print(f"{path.basename(__file__)}  @pconfig environment annotation normalization test passed.")
