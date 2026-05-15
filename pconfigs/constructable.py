# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Type, TypeVar, Union

from pconfigs.config import Config
from pconfigs.kwarg_mock import KwargMockConfig, NotMock
from pconfigs.kwarg_mock import Required as KwargMockRequired
from pconfigs.pinnable import Required, pconfig, pdefaults


@dataclass(repr=False)
class ConfigConstructableInterface(ABC):
    @abstractmethod
    def construct(self):
        pass


@dataclass(repr=False)
class ConfigConstructable(Config, ConfigConstructableInterface):
    typename: Type
    config: Config

    def construct(self) -> Type:
        return self.typename(self.config)


T = TypeVar("T")


@dataclass(repr=False)
class ConstructableConfig(Config, ConfigConstructableInterface):
    constructable_type: ClassVar[Type[T]]

    def construct(self) -> T:
        return self.constructable_type(config=self)


def get_constructable_config(config: Union[ConfigConstructable, ConstructableConfig]) -> Config:
    if isinstance(config, ConfigConstructable):
        return config.config
    elif isinstance(config, ConstructableConfig):
        return config
    else:
        raise ValueError(f"Unhandled config type: {type(config)}")


@dataclass(repr=False)
class KwargMockConfigConstructable(ConfigConstructable):
    config: KwargMockConfig

    def construct(self) -> Type:
        return self.typename(**self.config.to_args())


@dataclass(repr=False)
class KwargMockConstructableConfig(KwargMockConfig):
    config_version: ClassVar[int] = 0
    constructable_type: ClassVar[NotMock[Type[T]]]

    def construct(self, **required_kwargs) -> object:
        config_kwargs = self.to_args()
        for key, value in required_kwargs.items():
            if key in config_kwargs and config_kwargs[key] not in (KwargMockRequired, Required):
                raise ValueError(f"Cannot set {key} because the input config has already done so.")
            else:
                config_kwargs[key] = value

        for key, value in config_kwargs.items():
            if value is Required or value is KwargMockRequired:
                msg = (
                    f"A required parameter has not been passed to {type(self).__name__}.construct(). You must pass "
                    f"'{key} to construct {self.constructable_type.__name__}"
                )
                raise ValueError(msg)

        if self.config_version == 0:
            return self.constructable_type(**config_kwargs)
        elif self.config_version == 1:
            return self.constructable_type(config=self, **config_kwargs)
        else:
            msg = f"Unhandled config version. Got KwargMockConstructableConfig.config_version={self.config_version}"
            raise ValueError(msg)


@dataclass(repr=False)
class KwargMockFunction:
    """THIS IS DEPRECATED. USE KwargMockFunc."""

    funcname: Callable
    config: KwargMockConfig

    def __call__(self, *args, **kwargs):
        return self.funcname(
            *args,
            self.config.to_args(),
            **kwargs,
        )


@dataclass(repr=False)
class KwargMockFunc(KwargMockConfig):
    can_mock: ClassVar[bool] = True
    funcname: ClassVar[Callable[..., Any]]

    def __call__(self, *args, **kwargs):
        config_kwargs = self.to_args()
        for key, val in kwargs.items():
            if key in config_kwargs:
                msg = f"Cannot pass {key} as a kwarg. You must use the function config {type(self).__name__}."
                raise RuntimeError(msg)

        # Must use type(self).funcname because calling self.funcname passes self as the first arg to the function.
        return type(self).funcname(
            *args,
            **kwargs,
            **config_kwargs,
        )

    def construct(self) -> KwargMockFunc:
        return self


@pconfig
class NoneConfig(ConfigConstructableInterface):
    """A config whose ``construct()`` returns ``None``.

    ``NoneConfig`` is a singleton, mirroring Python's ``None``: every ``NoneConfig()`` call returns the same
    instance, so ``x is NoneConfig()`` works the same way ``x is None`` does.

    Use ``NoneConfig`` in a union with another constructable config to express an optional sub-config without
    forcing every constructor to write the verbose ternary pattern.

    Without ``NoneConfig`` (verbose, branches at every use site)::

        @pconfig(constructs=MyClass)
        class MyClassConfig:
            sub_config: Optional[SubConfig]

        @pconfiged
        class MyClass:
            def __init__(self):
                self.sub = (
                    self.config.sub_config.construct()
                    if self.config.sub_config is not None
                    else None
                )

    With ``NoneConfig`` (uniform, single ``construct()`` call)::

        @pconfig(constructs=MyClass)
        class MyClassConfig:
            sub_config: SubConfig | NoneConfig

        @pconfiged
        class MyClass:
            def __init__(self):
                self.sub = self.config.sub_config.construct()  # ``None`` when sub_config is NoneConfig()

    Callers turn the sub-config off by passing ``sub_config=NoneConfig()`` and turn it on by passing a real
    ``SubConfig(...)``. Both branches go through the same ``.construct()`` interface, so the consuming class
    does not need to know which case it received.
    """

    # Stored without a type annotation on purpose: an annotated ``ClassVar[NoneConfig]`` would make the
    # config print walker recurse into the singleton instance forever.
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Cannot use ``super()`` here: ``@pconfig`` rebuilds this class, so the implicit ``__class__`` cell
        # would point to the pre-decoration class and break the super chain. Call ``object.__new__`` directly.
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def construct(self) -> None:
        return None


pdefaults += NoneConfig()
