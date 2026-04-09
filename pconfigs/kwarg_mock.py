# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Generic, TypeVar, get_type_hints

try:
    from typing import get_origin
except ImportError:  # Python <3.8 fallback
    from typing_extensions import get_origin

from pconfigs.config import Config
from pconfigs.pinnable import Pinned
from pconfigs.sentinel import Sentinel

T = TypeVar("T")


class Overridden(Generic[T], metaclass=Sentinel):
    pass


class Required(Generic[T], metaclass=Sentinel):
    pass


class NotMock(Generic[T], metaclass=Sentinel):
    """Use this to mark dataclass fields that are not mocking kwargs that should be output by config.to_args()."""


class Kwarg(Generic[T], metaclass=Sentinel):
    """Use this to mark fields that are passed as non-docccumented parameters via a function or class' *kwargs """


class Omitted(Generic[T], metaclass=Sentinel):
    """Use this to mark fields that you want to omit from providing any value at all in the kwargs dict. This operates
    similarly to NotMock, but the meaning is different. NotMock embodies parameters that are not part of the mocked
    interface, and so should not be passed as kwargs. Omitted args are part of the mocked interface, but a value is not
    set for them. This allows you to use KwargMockConfigs that emulate the omission of args entirely, which adopts
    whatever unknown default might exist in the function/constructor you are calling.
    """


@dataclass(repr=False)
class KwargMockConfig(Config):
    """These configs have fields that are also configs, which will never be used by external classes. We use them
    to create kwarg dicts, and then discard them. This overload does the discarding so calling .asdict() will mock
    the args that you need to instantiate the class that is described by the config.
    """

    can_mock: ClassVar[bool] = False

    def asdict(self, use_proper_dataclass_field_getter: bool = True):
        return super().asdict(use_proper_dataclass_field_getter)

    def remove_subconfigs_(self, args: Dict[Any, Any]) -> Dict[Any, Any]:
        keys = list(args.keys())
        for key in keys:
            if isinstance(args[key], Config) and not getattr(args[key], "can_mock", False):
                # KwargMockFunc's are able to mock callables that are passed in as kwargs, so we check this "can_mock"
                # If you define new config classes, you can set can_mock=True as you see fit that are able to pretend
                # to act like some type that you are mocking.
                args.pop(key)

        return args

    def remove_non_mock_(self, args: Dict[Any, Any]) -> Dict[Any, Any]:
        hints = get_type_hints(type(self))
        for key in list(args.keys()):
            if key in hints and self._is_not_mock(hints[key]):
                args.pop(key)

        return args

    def _is_not_mock(self, field_type) -> bool:
        if not hasattr(field_type, "__origin__"):
            return False

        while get_origin(field_type) in (ClassVar, Pinned):
            field_type = field_type.__args__[0]

        is_not_mock = get_origin(field_type) == NotMock

        return is_not_mock

    def remove_omitted_(self, args: Dict[Any, Any]) -> Dict[Any, Any]:
        for key in list(args.keys()):
            if args[key] == Omitted:
                args.pop(key)

        return args

    def to_args(self, *properties: Dict[Any, Any]) -> Dict[Any, Any]:
        args = self.asdict()
        for prop in properties:
            args.update(getattr(self, prop))

        args = self.remove_non_mock_(args)
        args = self.remove_omitted_(args)
        args = self.remove_subconfigs_(args)

        return args

    def to_args_for_override(self, *overrides: str) -> Dict[Any, Any]:
        # Overload to_args to specify what properties should be included before overrides are pulled out.
        config = self.to_args()
        for override in overrides:
            if config[override] != Overridden:
                msg = "The field '{}' is overridden. Please acknowledge this by setting it to type Overridden."
                raise RuntimeError(msg.format(override))

            config.pop(override)

        return config

    def print_args(self, show_overridden: bool = False):
        args = self.to_args()
        maxlen = max([len(k) for k in args.keys()])
        for k, v in args.items():
            fmt = "{: >" + str(maxlen) + "} :  {}"
            print(fmt.format(k, v))
