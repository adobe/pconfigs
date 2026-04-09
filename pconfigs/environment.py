# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

import os
from dataclasses import dataclass
from enum import Enum
from types import SimpleNamespace
from typing import Any, ClassVar, Dict, Generic, List, Type, TypeVar, get_type_hints

from pconfigs.sentinel import Sentinel

T = TypeVar("T")


class NoDefault(Generic[T], metaclass=Sentinel):
    """Sentinel to mark env vars that do not have a default value. Don't use None. That's a reasonable default."""


@dataclass
class EnvVar:
    os_name: str
    default: Any
    helpstr: str = ""


class EnvironmentMetaclass(type):
    def get_info(cls, name: str) -> EnvVar:
        """Return information about the environment variable."""
        return super().__getattribute__(name)

    def _cast_to_bool(cls, value: Any) -> bool:
        if isinstance(value, str):
            value = value.lower()
            if value == "true" or value == "1":
                return True
            if value == "false" or value == "0":
                return False

        elif isinstance(value, int) or isinstance(value, float):
            return bool(value)

        raise RuntimeError("Unhandled representation of a bool: '{}'".format(value))

    def get_env_vars(cls) -> Dict[str, EnvVar]:
        envvars = {}
        for key in get_type_hints(cls):
            envvar = super().__getattribute__(key)
            envvars[key] = envvar

        return envvars

    def __getattribute__(cls, name):
        if name.startswith("__"):
            return super().__getattribute__(name)

        type_hints = get_type_hints(cls)
        if name not in type_hints:
            return super().__getattribute__(name)

        env_vars = cls.get_env_vars()
        env_var = env_vars[name]
        env_var_type = type_hints[name]
        env_var_value = os.environ.get(env_var.os_name)

        if env_var_value is None and env_var.default != NoDefault:
            env_var_value = env_var.default

        elif env_var_value is None:
            raise RuntimeError("Environment value for '{}' is not set.".format(name))

        if issubclass(env_var_type, Enum):
            # If the envvar is an enum, try to cast it to the enum type and report invalid values to the user.
            try:
                env_var_value = env_var_type(env_var_value)
            except ValueError as e:
                msg = "Environment variable '{}' cannot be set to '{}'. Valid values are {}."
                opts = ", ".join("'{}'".format(v.value) for v in env_var_type)
                raise ValueError(msg.format(env_var.os_name, env_var_value, opts)) from e

        elif env_var_value is not None:
            # cast from the os string value to the user's intended type for the property
            if env_var_type is bool:
                env_var_value = cls._cast_to_bool(env_var_value)
            else:
                env_var_value = env_var_type(env_var_value)

        return env_var_value

    def __str__(cls) -> str:
        out = cls.__name__ + "(\n"
        # This is implemented in the main class for public access
        out += "\n".join(cls.env_var_strings())
        out += "\n)"

        return out


class EnvironmentBase(metaclass=EnvironmentMetaclass):
    @classmethod
    def get_max_env_var_len(cls) -> int:
        env_vars = cls.get_env_vars()
        key_lens = []
        for key, env_var in env_vars.items():
            key_len = len(env_var.os_name)
            key_lens.append(key_len)

        return max(key_lens)

    @classmethod
    def env_var_strings(cls, fmt_prefix: str = "  ", fmt_suffix: str = " = ") -> List[str]:
        env_vars = cls.get_env_vars()
        max_env_var_len = cls.get_max_env_var_len()

        fmt = "{: <" + str(max_env_var_len) + "}"
        fmt = fmt_prefix + fmt + fmt_suffix + '"{}",'

        strings = []
        for key, env_var in env_vars.items():
            value = getattr(cls, key)
            if isinstance(value, Enum):
                value = value.value
            elif isinstance(value, bool):
                value = int(value)

            string = fmt.format(env_var.os_name, value)
            strings.append(string)

        return strings

    @classmethod
    def env_var_help(cls, fmt_prefix: str = "  ", fmt_suffix: str = " = ") -> str:
        fmt = "{: <" + str(cls.get_max_env_var_len()) + "}"
        fmt = fmt_prefix + fmt + fmt_suffix

        env_vars = cls.get_env_vars()
        max_value_len = max([len(str(getattr(cls, name))) for name in env_vars.keys()])
        fmt_value = "{: <" + str(max_value_len) + "}"

        strings = []
        for name, env_var in cls.get_env_vars().items():
            value = getattr(cls, name)
            value = "" if value is None else value
            string = fmt.format(env_var.os_name) + fmt_value.format(value) + " -- " + env_var.helpstr
            strings.append(string)

        return "\n".join(strings)
