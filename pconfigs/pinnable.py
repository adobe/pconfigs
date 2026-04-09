# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

import ast
import collections
import collections.abc
import hashlib
import inspect
import re
import sys
import types
import typing
from copy import copy
from dataclasses import dataclass, fields
from enum import Enum
from functools import wraps
from graphlib import CycleError, TopologicalSorter
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)
from warnings import warn

from pconfigs.config import Config, MemoizedCall, get_fields_memoized
from pconfigs.sentinel import Sentinel, SentinelOperationError

__all__ = [
    "Pin",
    "Pinned",
    "Required",
    "pconfig",
    "pconfiged",
    "pdefaults",
    "pproperty",
    "pinputs",
    "penum",
    "penv",
]


T = TypeVar("T")


get_type_hints_memoized = MemoizedCall(get_type_hints)


class Pinned(Generic[T], metaclass=Sentinel):
    pass


class Required(Generic[T], metaclass=Sentinel):
    pass


class NotUsed(Generic[T], metaclass=Sentinel):
    pass


class Pin:
    def __init__(self, value):
        self.value = value

    def strip(self):
        return self.value

    def __str__(self):
        return "Pin({})".format(self.value)


class PropInputs:
    """facilitates dot access for inputs"""

    def __init__(self):
        self.input_names = set()

    def __contains__(self, name):
        return hasattr(self, name)

    def __len__(self):
        return len(self.input_names)

    @property
    def names(self) -> List[str]:
        return list(self.input_names)

    def add(self, name, value):
        self.input_names.add(name)
        setattr(self, name, value)

    def remove(self, name):
        self.input_names.remove(name)
        delattr(self, name)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)


@dataclass(repr=False)
class PinnableConfig(Config):
    # Default instance registrar; subclasses may get a more specific annotation via pdefault
    default_config: ClassVar[PinnableConfig] = None

    def skip_print_key(self, key: str) -> bool:
        if key in (
            "default_config",
            "autocopy_shared_ancestors",
            "use_legacy_new_operator",
            "can_mock",
            "config_version",
        ):
            return True

        return super().skip_print_key(key)

    def _is_field(self, name: str):
        for field in get_fields_memoized(type(self)):
            if field.name == name:
                return True

        return False

    def _get_field_type(self, name: str) -> Type:
        for field in get_fields_memoized(type(self)):
            if field.name == name:
                return field.type

        raise ValueError("Field not found: {}".format(name))

    def _is_property(self, name: str) -> bool:
        return hasattr(type(self), name)

    @classmethod
    def _is_pinned(cls, field_type) -> bool:
        if not hasattr(field_type, "__origin__"):
            return False

        is_pinned = field_type.__origin__ == Pinned

        return is_pinned

    def _is_config(self, field_type) -> bool:
        return inspect.isclass(field_type) and issubclass(field_type, Config)

    def mark_pins_(self) -> PinnableConfig:
        self._mark_pins = True
        self._unset_pins = False
        self._return_inputs = False
        return self

    def mark_pins(self) -> PinnableConfig:
        return copy(self).mark_pins_()

    def unset_pins_(self) -> PinnableConfig:
        self._mark_pins = False
        self._unset_pins = True
        self._return_inputs = False
        return self

    def unset_pins(self) -> PinnableConfig:
        return copy(self).unset_pins_()

    def inputs_(self) -> PinnableConfig:
        """CAUTION. If you import a config and run this on that config, all future imports of the same config path will
        return property inputs, rather than the computed property values, because you will have mutated the config state
        """
        self._unset_pins = False
        self._mark_pins = False
        self._return_inputs = True
        return self

    @property
    def inputs(self) -> PinnableConfig:
        return copy(self).inputs_()

    @classmethod
    def make_with_all_required(cls) -> PinnableConfig:
        inputs = {}
        hints = get_type_hints_memoized(cls)
        for field in get_fields_memoized(cls):
            field_type = hints[field.name]
            value = Pinned if cls._is_pinned(field_type) else Required
            inputs[field.name] = value

        return cls(**inputs)

    def _throw_if_pinned(self, name: str, value: Any):
        """Throw value error if field with name 'name' is pinned but being set inappropriately."""

        field_type = get_type_hints_memoized(type(self))[name]
        if self._is_pinned(field_type) and type(value) != Pin and value != Pinned:
            config_type_name = type(self).__name__
            raise ValueError(f"Cannot set a pinned field. Use {config_type_name}.{name}=Pinned to fix this error.")

    def __setattr__(self, name, value):
        if self._is_field(name) and not self._is_property(name):
            self._throw_if_pinned(name, value)
            if type(value) == Pin:
                value = value.strip()

        super().__setattr__(name, value)

    def __getattribute__(self, name):
        value = object.__getattribute__(self, name)
        try:
            type_hints = get_type_hints_memoized(type(self))
        except NameError as e:
            if "name 'Pinned' is not defined" in str(e):
                msg = (
                    f"This error probably occurred because a pinned field in {type(self).__name__} was defined "
                    "without importing the Pinned sentinel (e.g., from pconfigs import Pinned)."
                )
                raise ValueError(msg) from e

            raise

        if name in type_hints:
            field_type = type_hints[name]
            # We can't set a default value of _mark_pins in the constructor because dataclasses define the constructor,
            # not us. So, we use the absence of the flag to also indicate False.
            field_is_pinned = self._is_pinned(field_type)
            mark_pins = hasattr(self, "_mark_pins") and self._mark_pins
            unset_pins = hasattr(self, "_unset_pins") and self._unset_pins
            return_inputs = hasattr(self, "_return_inputs") and self._return_inputs
            if field_is_pinned and (mark_pins or return_inputs) and type(value) != Pin and value != Pinned:
                value = Pin(value)

            elif field_is_pinned and unset_pins:
                value = Pinned

        return value

    class PropInputs:
        def __init__(self, deps: Union[List[str], str] = None, inputs_attr: str = "pinputs"):
            self.inputs_attr = inputs_attr
            if deps is None:
                self.field_names = []
            elif isinstance(deps, str):
                self.field_names = [deps]
            else:
                self.field_names = deps

        def __call__(self, prop):
            self.prop_name = prop.fget.__name__
            if self.prop_name == "_inputs_attrs":
                raise ValueError("The name '_inputs_attrs' is reserved in PinnableConfig classes.")

            @wraps(prop.fget)
            def fget(slf):
                return_inputs = hasattr(slf, "_return_inputs") and slf._return_inputs
                pinputs = getattr(slf, self.inputs_attr)

                if return_inputs and self.prop_name in pinputs:
                    return getattr(pinputs, self.prop_name)

                # Handle the case when a prop input is "Required" and is input to a prop func of the same name.
                if self.prop_name in pinputs and getattr(pinputs, self.prop_name) is Required:
                    return Required

                for field_name in self.field_names:
                    if field_name == prop.fget.__name__:
                        # TODO: We need to allow for the case when a property lists itself as required to compute itself.
                        # This should occur when a property requires the user to pass an incomplete version of itself
                        # as input (to specify free parameters). In that case, we need to fetch the value from the
                        # user inputs object, but this PropDependencies object does't know about that. The solution is
                        # to write a single @pproperty decorator that does both things. If we don't continue here, it
                        # is an infinite loop of trying to get ourselves to construct ourselves.
                        continue

                    value = getattr(slf, field_name)
                    if value == Required or value == Pinned:
                        return Pinned

                if self.prop_name in slf.__dict__:
                    return slf.__dict__[self.prop_name]  # memoized

                if self.prop_name in pinputs:
                    try:
                        slf.__dict__[self.prop_name] = prop.fget(slf)
                    except SentinelOperationError:
                        # This often obviates the dependency list, but there are still cases were users encounter
                        # strange behavior unless dependencies are passed.
                        slf.__dict__[self.prop_name] = Pinned

                    return slf.__dict__[self.prop_name]

                raise ValueError("Unknown property: {}.{}".format(type(slf).__name__, self.prop_name))

            @wraps(prop.fset)
            def fset(slf, value):
                if not hasattr(slf, "_inputs_attrs"):
                    slf._inputs_attrs = set()

                slf._inputs_attrs.add(self.inputs_attr)

                if not hasattr(slf, self.inputs_attr):
                    setattr(slf, self.inputs_attr, PropInputs())

                slf._throw_if_pinned(self.prop_name, value)
                if type(value) == Pin:
                    value = value.strip()

                getattr(slf, self.inputs_attr).add(self.prop_name, value)

            # Add the deps to the fget function so the config class can check for circular dependencies.
            setattr(fget, "__pconfig_prop_deps__", list(self.field_names))

            return property(fget=fget, fset=fset, fdel=prop.fdel)

    def __post_init__(self):
        super().__post_init__()

        # If the dataclass has properties that require inputs, we exercise each property getter
        # in order to complete the construction process. Then we discard the inputs.
        #
        # Technically, the user could overload __post_init__ themselves to fixup (aka pin)
        # properties that have been passed in from (say) a base config, but that obfuscates
        # what the changes are for anyone reading the implementation. By using PropInputs,
        # this generic __post_init__ eliminates a lot of redundant overhead code. The user simply
        # writes a property function, decorates it PinnableConfig.PropInputs(), and accesses
        # the property inputs inside their property function.
        if hasattr(self, "_inputs_attrs"):
            for inputs_attr in self._inputs_attrs:
                pinputs = getattr(self, inputs_attr)
                for name in pinputs.names:
                    getattr(self, name)

    class PropDependencies:
        def __init__(self, *field_names: str):
            self.field_names = field_names

        def __call__(self, prop):
            @wraps(prop.fget)
            def fget(slf):
                for field_name in self.field_names:
                    if field_name == prop.fget.__name__:
                        # TODO: We need to allow for the case when a property lists itself as required to compute itself.
                        # This should occur when a property requires the user to pass an incomplete version of itself
                        # as input (to specify free parameters). In that case, we need to fetch the value from the
                        # user inputs object, but this PropDependencies object does't know about that. The solution is
                        # to write a single @pproperty decorator that does both things. If we don't continue here, it
                        # is an infinite loop of trying to get ourselves to construct ourselves.
                        continue

                    value = getattr(slf, field_name)
                    if value == Required or value == Pinned:
                        return Pinned

                return prop.fget(slf)

            return property(fget=fget, fset=prop.fset, fdel=prop.fdel)


class PConfig(PinnableConfig):
    pass


class _PDefaults(type):
    def __iadd__(cls, config: PinnableConfig, auto_generated: bool = False) -> _PDefaults:
        if not isinstance(config, PinnableConfig):
            raise TypeError("pdefaults expects a @pconfig instance for '+=' assignment.")

        config_cls = type(config)

        # Allow user to set a default config only if there is no existing default or if the existing default is strictly
        # a parent config type. This allows the user to use auto-copy when they create default configs for derived
        # config types.
        if config_cls.default_config is not None:
            existing_type = type(config_cls.default_config)
            is_ancestor = config_cls is not existing_type and issubclass(config_cls, existing_type)
            if not is_ancestor:
                # Users can override default configs that are auto-generated by the pconfig system (kwarg-mocks)
                old_cfg = config_cls.default_config
                old_cfg_auto_generated = getattr(old_cfg, "__pconfig_auto_generated__")

                # Permit update when same type and only Required fields are being set/changed. This supports KwargMock
                # cases where the user wants to add new fields to the mocked class. Those fields will get auto-defaulted
                # to Required until the user updates them via this code path here.
                expected_err = (
                    f"The default config for {config_cls.__name__} is already set. You can't make 2 defaults."
                )
                if not old_cfg_auto_generated and config_cls is existing_type:
                    # If there are no Required fields left, disallow redefining defaults
                    has_required = any(getattr(old_cfg, f.name) is Required for f in get_fields_memoized(config_cls))
                    if not has_required:
                        raise ValueError(expected_err)

                    new_cfg = config
                    # Validate only fields that were Required in old default are changed
                    for f in get_fields_memoized(config_cls):
                        old_val = getattr(old_cfg, f.name)
                        new_val = getattr(new_cfg, f.name)
                        if old_val is Required:
                            continue

                        if new_val != old_val:
                            msg = (
                                f"pdefaults: cannot change previously-set default for field '{f.name}' "
                                f"in {config_cls.__name__}. Only fields that were Required may be updated."
                            )
                            raise ValueError(msg)

                elif not old_cfg_auto_generated:
                    raise ValueError(expected_err)

        setattr(config, "__pconfig_auto_generated__", auto_generated)
        config_cls.default_config = config

        return cls

    # Support call: pdefaults(TestConfig) -> TestConfig.default_config
    def __call__(cls, config: Type[PinnableConfig] | PinnableConfig) -> PinnableConfig:
        # Accept either a config class or an instance; normalize to class
        if isinstance(config, PinnableConfig):
            config_cls = type(config)
        elif isinstance(config, type) and issubclass(config, PinnableConfig):
            config_cls = config
        else:
            raise TypeError("pdefaults expects a @pconfig class or instance when called")

        return config_cls.default_config


class pdefaults(metaclass=_PDefaults):
    """Singleton class for registering and retrieving default configs.

    See also:
        For examples, see :ref:`examples/construction:Construction`.

    This class manages the default config instance for @pconfig classes.

    * ``pdefaults += MyConfig(...)`` sets ``MyConfig.default_config`` to the
      given instance. Only one default is allowed per config type; attempting
      to set multiple defaults raises an error, with special rules for
      auto-generated defaults and subclasses.
    * ``default_config = pdefaults(MyConfig)`` or ``pdefaults(config_instance)`` returns the default config for this type.

    """

    pass


def pinputs(config: PinnableConfig) -> PropInputs:
    """Return the property inputs for a pconfig instance.

    See also:
        For examples, see :ref:`subsec-modify-user-input-values-with-pinputs`.

    Args:
        config (PConfig): A pconfig object (i.e., an instance of a class decorated with ``@pconfig``) whose property
        inputs should be retrieved.

    Returns:
        :class:`PropInputs`: A container of property input values that can be accessed via attribute (dot) access.
    """
    return config.pinputs


class KwargMockType(Enum):
    Null = "null"
    Function = "function"
    External = "external"  # Externally defined classes that are imported.
    Derived = "derived"  # Classes that are derived from external classes.


def dataclass_stubbed(
    cls,
    legacy_stub: Type[PConfig] = None,
    dataclass_kwargs: Dict[str, Any] = None,
    stub_prefix: str = "Stubbed",
):
    """Core logic to create a stub dataclass and re-base cls to inherit from it.

    Ensures the visible class is also a dataclass with no own fields so that
    dataclasses.fields(cls) and static tooling work as expected.
    """
    dataclass_kwargs = {} if dataclass_kwargs is None else dataclass_kwargs

    annotations = dict(getattr(cls, "__annotations__", {}))

    PriorStubCls = None
    if hasattr(cls, "__is_pconfig_stub__"):
        # If an ancestor class is a stub config, we will have this __is_pconfig_stub__ attribute. Find the first
        # ancestor class that has this attribute set to True. We must create a new stub that inherits from it.
        for prior_cls in cls.mro():
            if getattr(prior_cls, "__is_pconfig_stub__", None) is True:
                PriorStubCls = prior_cls
                break

        if PriorStubCls is None:
            raise RuntimeError(f"No stub class found in the mro for {cls.__name__}. This seems impossible.")

    elif legacy_stub is not None:
        PriorStubCls = legacy_stub

    # Create stub class, which only has the annotations (not any property objects that shadow those annotations)
    def exec_stub(ns):
        ns["__module__"] = cls.__module__
        ns["__qualname__"] = f"{stub_prefix}{cls.__qualname__}"
        ns["__doc__"] = cls.__doc__
        ns["__annotations__"] = annotations
        ns["__is_pconfig_stub__"] = True

    if PriorStubCls is None:
        StubCls = types.new_class(f"{stub_prefix}{cls.__name__}", cls.__bases__, {}, exec_stub)
    else:
        StubCls = types.new_class(f"{stub_prefix}{cls.__name__}", (PriorStubCls,), {}, exec_stub)

    StubCls = dataclass(**(dataclass_kwargs or {}))(StubCls)

    # Final class inherits from stub; inject original attributes in namespace so descriptors get __set_name__
    def exec_final(ns):
        ns["__module__"] = cls.__module__
        ns["__qualname__"] = cls.__qualname__
        ns["__doc__"] = cls.__doc__
        ns["__is_pconfig_stub__"] = False
        # Do not include annotations at this level to avoid redeclaring fields
        for key, val in cls.__dict__.items():
            if key in ("__dict__", "__weakref__", "__annotations__", "__module__", "__doc__", "__qualname__"):
                continue
            ns[key] = val

    if PriorStubCls is None:
        # First case (no prior stub): StubCls already inherits cls.__bases__, so the visible class can be
        # PropsCls(StubCls,) and still include all original bases through the stub chain.
        PropsCls = types.new_class(cls.__name__, (StubCls,), {}, exec_final)
    else:
        # Second case (prior stub): StubCls only inherits PriorStubCls (not cls.__bases__). To retain any non-stub bases
        # on cls, PropsCls must inherit cls.__bases__ + (StubCls,). If you switched to always PropsCls(StubCls,) here,
        # you’d drop those non-stub bases.
        PropsCls = types.new_class(cls.__name__, cls.__bases__ + (StubCls,), {}, exec_final)

    # Make the visible class a dataclass too (with no own fields) so dataclasses.fields(PropsCls)
    # correctly aggregates fields from base dataclasses and the stub, including newly introduced ones.
    PropsCls = dataclass(**(dataclass_kwargs or {}))(PropsCls)

    return PropsCls


# Helper for @pconfig
def _ensure_pconfig_inheritance(cls):
    if issubclass(cls, PConfig):
        return cls

    def exec_body(ns):
        ns["__module__"] = cls.__module__
        ns["__qualname__"] = cls.__qualname__
        ns["__doc__"] = cls.__doc__
        # preserve annotations at this level because this is the only class (no stub)
        ns["__annotations__"] = dict(getattr(cls, "__annotations__", {}))
        for key, val in cls.__dict__.items():
            if key in ("__dict__", "__weakref__", "__annotations__", "__module__", "__doc__", "__qualname__"):
                continue
            ns[key] = val

    return types.new_class(cls.__name__, (PConfig,) + cls.__bases__, {}, exec_body)


# Helper for @pconfig
def _validate_no_instance_defaults(cls: Type):
    # Operate on raw __annotations__ to enforce only the ClassVar default rule. Cannot use get_type_hints because
    # we cannot assume that all forward type references can be resolved---the user's decorator might be in the middle
    # of their code, with subsequent type definitions below. Still, we must detect class vars and ignore them when
    # we check if their class is setting default values for the annotated fields.
    annotations_raw = getattr(cls, "__annotations__", {})
    classvar_names = set()
    for fname, anno in annotations_raw.items():
        if isinstance(anno, str):
            stripped = re.sub(r"\s+", "", anno)
            if stripped.startswith("ClassVar[") or stripped.startswith("typing.ClassVar["):
                classvar_names.add(fname)
        else:
            try:
                if get_origin(anno) is ClassVar:
                    classvar_names.add(fname)
            except Exception:
                pass

    for name in annotations_raw.keys():
        if name in classvar_names:
            continue
        if name in cls.__dict__ and not isinstance(cls.__dict__[name], property):
            msg = (
                f"@pconfig fields cannot have default values unless annotated as ClassVar: field "
                f"'{name}' in {cls.__name__}"
            )
            raise TypeError(msg)

    return cls


# Helper for @pconfig: convert annotations of EnvironmentBase subclasses into ClassVar[Type[T]]
def _normalize_environment_annotations(cls: Type) -> Type:
    annotations_raw = dict(getattr(cls, "__annotations__", {}))
    if not annotations_raw or "environment" not in annotations_raw:
        return cls

    env_anno = annotations_raw.get("environment")
    from pconfigs.environment import EnvironmentBase

    env_type = None
    if isinstance(env_anno, type):
        env_type = env_anno
    elif isinstance(env_anno, str):
        try:
            module = sys.modules.get(cls.__module__)
            eval_globals = dict(getattr(module, "__dict__", {}))
            eval_globals.setdefault("ClassVar", ClassVar)
            eval_globals.setdefault("Type", Type)
            eval_globals.setdefault("typing", sys.modules.get("typing"))
            eval_globals.setdefault("__builtins__", getattr(module, "__builtins__", __import__("builtins")))
            env_type = eval(env_anno, eval_globals, eval_globals)
        except Exception as e:
            msg = (
                f"@pconfig: You have specified an annotation called 'environment' on '{cls.__name__}', but it could "
                f"not be resolved from a string into a type. Please ensure the type is imported and not a forward "
                f"reference. Original error: {e}"
            )
            raise TypeError(msg) from e

    # If the resolved type is not an EnvironmentBase subclass, do nothing
    if not (isinstance(env_type, type) and issubclass(env_type, EnvironmentBase)):
        msg = (
            f"@pconfig: You have specified an an annotation called 'environment' on '{cls.__name__}' that is not a "
            "class that is created by @penv (it is not a subclass of EnvironmentBase). Please note that 'environment' "
            "is a reserved name in pconfigs. You must use a different name if you are not intending to create an "
            "environment field."
        )
        raise ValueError(msg)

    # Build new class with updated annotations and defaults for the env field
    def exec_body(ns):
        ns["__module__"] = cls.__module__
        ns["__qualname__"] = cls.__qualname__
        ns["__doc__"] = cls.__doc__

        # Update annotations: env field becomes ClassVar[Type[T]]
        updated_annotations = dict(annotations_raw)
        updated_annotations["environment"] = ClassVar[Type[env_type]]  # type: ignore[index]
        ns["__annotations__"] = updated_annotations

        # Copy original attributes, skipping env field value (we'll set it explicitly)
        for key, val in cls.__dict__.items():
            if key in ("__dict__", "__weakref__", "__annotations__", "__module__", "__doc__", "__qualname__"):
                continue
            if key == "environment":
                continue
            ns[key] = val

        # Set env field default to its class type
        ns["environment"] = env_type

    return types.new_class(cls.__name__, cls.__bases__, {}, exec_body)


# Helper for @pconfig
def _class_needs_stubbing(cls) -> bool:
    annotations = getattr(cls, "__annotations__", {})
    for name in annotations.keys():
        if name in cls.__dict__ and isinstance(cls.__dict__[name], property):
            return True

    if hasattr(cls, "__is_pconfig_stub__"):
        return True

    return False


# Helper for @pconfig
def _validate_constructable_class(config_cls, constructable_type):
    if constructable_type is None:
        return
    if inspect.isfunction(constructable_type) or inspect.ismethod(constructable_type):
        return
    if getattr(constructable_type, "__kwarg_mock__", False):
        return

    if not getattr(constructable_type, "__is_pconfiged__", False):
        msg = (
            f"@pconfig: config class '{config_cls.__name__}' cannot construct class '{constructable_type.__name__}' "
            f"because it is not pconfiged. Did you use @pconfiged on '{constructable_type.__name__}'?"
        )
        raise TypeError(msg)

    annotations = getattr(constructable_type, "__annotations__", {})
    if "config" not in annotations:
        raise TypeError(f"@pconfig: {constructable_type.__name__} must declare an annotation 'config: <ConfigType>'.")

    config_anno = annotations["config"]
    if isinstance(config_anno, str):
        expected_name = config_anno
    elif isinstance(config_anno, type):
        expected_name = config_anno.__name__
    else:
        raise TypeError(f"@pconfig: unsupported config annotation on {constructable_type.__name__}: {config_anno}")

    if expected_name != config_cls.__name__:
        raise TypeError(
            f"@pconfig: the @pconfiged type '{constructable_type.__name__}' expects a config of type "
            f"'{expected_name}', not '{config_cls.__name__}'."
        )


# Helper for @pconfig
def _is_function_like(callable_):
    return (
        inspect.isfunction(callable_)
        or inspect.ismethod(callable_)
        or getattr(callable_, "__kwarg_mock__", None) is KwargMockType.Function
    )


# Helper for @pconfig
def _conditionally_warn_about_missing_pconfiged_decorator(self, others, kwargs):
    """Users might forget to decorate their constructable classes with @pconfiged. When they do that, they will get
    an esoteric NameError that will not indicate the problem. We therefore catch the situation and warn them.
    """
    if not kwargs and len(others) == 1 and isinstance(others[0], type):

        def get_type_location(tp):
            try:
                path = inspect.getsourcefile(tp) or inspect.getfile(tp)
                _, lineno = inspect.getsourcelines(tp)
                return path, str(lineno)
            except (OSError, TypeError):
                mod = inspect.getmodule(tp)
                return getattr(mod, "__file__", None), None

        self_type = type(self).__name__
        other_type = others[0].__name__
        typelen = max(len(self_type), len(other_type))
        msg = (
            f"@pconfig: class '{self_type}' is being constructed as a pconfig class, and received "
            f"received a single argument of type '{other_type}'. This is an unusual config pattern that could "
            f"indicate a bug. Is '{self_type}' "
            f"supposed to be a pconfig class? If not, you probably need to decorate '{self_type}' with "
            f"@pconfiged.\n See:\n  {self_type: >{typelen}s} at {':'.join(get_type_location(type(self)))}\n"
            f"  {other_type: >{typelen}s} at {':'.join(get_type_location(others[0]))}\n\n"
            f"If this is not a bug, you can suppress this warning by constructing your config with a kwarg "
            f"rather than a positional argument.\n"
        )
        warn(msg)


# Helper for _augment_annotations_from_constructable_init()
def _annotations_equivalent(a: Any, b: Any) -> bool:
    if a is b:
        return True
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    try:
        from typing import get_args, get_origin

        origin_a, origin_b = get_origin(a), get_origin(b)
        # If either is a typing construct, compare origins and args
        if origin_a is not None or origin_b is not None:
            if origin_a != origin_b:
                return False
            args_a, args_b = get_args(a), get_args(b)
            if len(args_a) != len(args_b):
                return False
            return all(_annotations_equivalent(x, y) for x, y in zip(args_a, args_b))
    except Exception:
        pass

    # Fallbacks: direct equality or name equality for bare classes
    if a == b:
        return True
    name_a = getattr(a, "__name__", None)
    name_b = getattr(b, "__name__", None)
    return name_a is not None and name_a == name_b


def _is_simply_typed(annotation: Any, top_level: bool = True) -> bool:
    """Check if a type annotation is simply typed for config purposes.

    Simply typed means: a simple scalar (str, int, float, bool, bytes, pathlib.Path, Enum subclass),
    a Literal, a simple container of simple types (list, tuple, dict, set, frozenset, and their
    abstract counterparts Sequence, MutableSequence, Mapping, MutableMapping, MutableSet with simple
    element types), or an Optional/Union thereof.

    At the top level, a Union is simply typed if any non-None component is simply typed (reflecting
    function overload conventions where different overloads may accept different types). Inside
    containers, all components must be simply typed.
    """
    import pathlib

    simple_scalar_types = (str, int, float, bool, bytes, pathlib.Path, pathlib.PurePath)
    simple_container_types = (
        list,
        tuple,
        dict,
        set,
        frozenset,
        collections.abc.Sequence,
        collections.abc.MutableSequence,
        collections.abc.Mapping,
        collections.abc.MutableMapping,
        collections.abc.MutableSet,
    )

    if annotation in simple_scalar_types or annotation in simple_container_types:
        return True

    if inspect.isclass(annotation) and issubclass(annotation, Enum):
        return True

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Literal:
        return True

    if origin is Union:
        non_none_args = [a for a in args if a is not type(None)]
        if not non_none_args:
            return False

        if top_level:
            return any(_is_simply_typed(a, top_level=False) for a in non_none_args)
        else:
            return all(_is_simply_typed(a, top_level=False) for a in non_none_args)

    if origin in simple_container_types:
        if not args:
            return True

        return all(_is_simply_typed(a, top_level=False) for a in args)

    return False


def _has_simply_typed_default(default: Any) -> bool:
    """Check if a default value is simply typed.

    None is considered simply typed because it is the standard default for optional parameters.
    Simple scalars (str, int, float, bool, bytes, pathlib.Path, Enum members) are simply typed.
    Containers (list, tuple, dict, set, frozenset) are simply typed only if all of their elements
    are recursively simply typed.
    """
    import pathlib

    if default is inspect.Parameter.empty:
        return False

    if default is None:
        return True

    if isinstance(default, (str, int, float, bool, bytes, pathlib.PurePath, Enum)):
        return True

    if isinstance(default, dict):
        return all(_has_simply_typed_default(k) and _has_simply_typed_default(v) for k, v in default.items())

    if isinstance(default, (list, tuple, set, frozenset)):
        return all(_has_simply_typed_default(element) for element in default)

    return False


# Helper for @pconfig
def _augment_annotations_from_constructable_init(config_cls: Type, func: Callable, type_name: str) -> None:
    """Augment config_cls.__annotations__ using a function signature.

    - Reads parameters from the provided func
    - Creates type annotations for parameters
    - Does NOT set defaults; only adjusts annotations

    A parameter is auto-added as a config field when:

    1. It is not positional-only (config params must be named).
    2. It has a simply-typed annotation and a simply-typed default.

    Parameters that are explicitly annotated on the config class are always included regardless of
    these rules, allowing users to opt in to any parameter they need.
    """
    sig = inspect.signature(func)

    existing_annotations = dict(getattr(config_cls, "__annotations__", {}))
    new_annotations: dict[str, Any] = {}

    # Calling get_type_hints resolves the annotation types, rather than leaving those annotations as strings. On the
    # other hand, the param.annotation values that one gets from sig.parameters.values() are not necessarily resolved
    # types (they can be strings). This causes a bug: the user tries to construct their class, and our pconfig
    # constructor calls get_type_hints(), which tries to resolve those simple string types from param.annotation, but
    # it cannot do so because the type definitions are not in the user's module where they define config_cls.
    # If however we call get_type_hints() now using func.__globals__, we can resolve the types from the annotation
    # strings. This allows the user to then call simple "get_type_hints(config_cls)" on the config class and get all the
    # typehints without having access to func.__globals__.
    #
    # Make sure we have as many types as we can get to try to resolve the type hints in the user's function
    # Sometimes types aren't actually imported into the module that uses those annotations. One example is the pytorch
    # DataLoader class, which only imports "Iterable" if some condition is met that is not actually met when you import.
    gloablns = dict(getattr(func, "__globals__", {}))
    gloablns.update(vars(typing))
    gloablns.update(vars(collections.abc))
    try:
        func_hints = get_type_hints(func, globalns=gloablns)
    except NameError as e:
        msg = (
            f"Unable to get type hints for {func.__qualname__} because a typename could not be resolved: {e}. "
            "If you defined this function, make sure that you have imported all of the typehint types. If it is "
            "defined by a library, you can make a derived class and re-specify the interface with fully resolved types."
        )
        raise NameError(msg)

    for param in sig.parameters.values():
        if param.name == "self":
            continue

        if param.name in existing_annotations:
            ann = existing_annotations[param.name]
            new_annotations[param.name] = ann
            continue

        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            continue

        if param.default is inspect.Parameter.empty:
            continue

        ann = func_hints[param.name] if param.name in func_hints else param.annotation
        if ann is inspect.Signature.empty:
            ann = type(param.default)

        is_simply_typed = _is_simply_typed(ann)
        has_simply_typed_default = _has_simply_typed_default(param.default)

        if not is_simply_typed or not has_simply_typed_default:
            preamble = f"Parameter '{param.name}' of {type_name}"
            configurable_fix = f"  {param.name}: <simple_type>   # add with a simple type to make it configurable"
            omit_fix = f"  {param.name}: Omitted[<type>]  # explicitly omit it from the config"

            if ann is type(None):
                detail = (
                    "has no type annotation and defaults to None, so its intended type is unknown. "
                    f"Look up the intended type and add it to {config_cls.__name__}:"
                )
            elif not is_simply_typed and not has_simply_typed_default:
                detail = (
                    f"has a non-simple type annotation ({ann!r}) and a non-simple default value "
                    f"({param.default!r}). Config fields must use simple types. "
                    f"Add one of these to {config_cls.__name__}:"
                )
            elif not is_simply_typed:
                detail = (
                    f"has a non-simple type annotation ({ann!r}). Config fields must use simple types. "
                    f"Narrow it to a simple type or omit it by adding one of these to {config_cls.__name__}:"
                )
            else:
                detail = (
                    f"has a non-simple default value ({param.default!r}). Config field defaults must be "
                    f"simple values. Provide a simple default or omit it by adding one of these to "
                    f"{config_cls.__name__}:"
                )

            raise TypeError(f"{preamble} {detail}\n{configurable_fix}\n{omit_fix}")

        new_annotations[param.name] = ann

    # Append any remaining existing annotations (user-declared) preserving their relative order
    # and mark them as NotMock[...] so they are excluded from KwargMock to_args
    from pconfigs.kwarg_mock import Kwarg, NotMock

    not_mock_hint_injected_into_module = False
    for key, val in existing_annotations.items():
        if key in new_annotations:
            continue
        try:
            current_origin = get_origin(val)
        except Exception:
            current_origin = None

        if current_origin is ClassVar or val.startswith("ClassVar["):
            continue

        if isinstance(val, str):
            s = val.strip()
            if s.startswith("Kwarg["):
                wrapped = val
            elif s.startswith("NotMock["):
                wrapped = val
            else:
                wrapped = f"NotMock[{val}]"

        elif current_origin is Kwarg:
            wrapped = val
        elif current_origin is NotMock:
            wrapped = val
        else:
            wrapped = NotMock[val]

        # Ensure NotMock is available in the module where the class is defined so string annotations can resolve
        if not not_mock_hint_injected_into_module:
            mod = sys.modules.get(config_cls.__module__)
            if mod is not None and not hasattr(mod, "NotMock"):
                setattr(mod, "NotMock", NotMock)

            not_mock_hint_injected_into_module = True

        new_annotations[key] = wrapped

    if new_annotations:
        setattr(config_cls, "__annotations__", new_annotations)


def _annotation_keys_mro(cls):
    keys = []
    for base in reversed(cls.__mro__):  # parents first
        ann = getattr(base, "__annotations__", {}) or {}
        for k in ann:
            if k not in keys:
                keys.append(k)
    return keys


# Helper for pconfig
def _throw_on_circular_property_dependencies(cls: Type):
    # Detect circular property dependencies and throw at class-definition time.
    dependencies = {}
    for key in _annotation_keys_mro(cls):
        value = inspect.getattr_static(cls, key, None)
        if value is not None and isinstance(value, property) and hasattr(value.fget, "__pconfig_prop_deps__"):
            dependencies[key] = value.fget.__pconfig_prop_deps__

    try:
        tuple(TopologicalSorter(dependencies).static_order())
    except CycleError as e:
        if len(e.args) > 1:
            cycle = " -> ".join(reversed(e.args[1]))
            msg = "@pconfig: {} has circular property dependencies: {}"
            raise ValueError(msg.format(cls.__name__, cycle))

        msg = f"@pconfig: Failed to analyze the property dependency graph for {cls.__name__}."
        raise RuntimeError(msg) from e


# Helper for pconfig
def _ensure_constructable_inheritance(cls: Type, _callable: Callable):
    # Ensure the resulting class derives from the right constructable base
    if (
        inspect.isfunction(_callable)
        or inspect.ismethod(_callable)
        or getattr(_callable, "__kwarg_mock__", None) is KwargMockType.Function
    ):
        from pconfigs.constructable import KwargMockFunc as ConstructBase
    elif _callable.__kwarg_mock__ not in (KwargMockType.Null, KwargMockType.Function):
        from pconfigs.constructable import KwargMockConstructableConfig as ConstructBase
    else:
        from pconfigs.constructable import ConstructableConfig as ConstructBase

    if not issubclass(cls, ConstructBase):

        def exec_body(ns):
            ns["__module__"] = cls.__module__
            ns["__qualname__"] = cls.__qualname__
            ns["__doc__"] = cls.__doc__
            ns["__annotations__"] = dict(getattr(cls, "__annotations__", {}))
            for key, val in cls.__dict__.items():
                if key in ("__dict__", "__weakref__", "__annotations__", "__module__", "__doc__", "__qualname__"):
                    continue
                ns[key] = val

        cls = types.new_class(cls.__name__, (ConstructBase,) + cls.__bases__, {}, exec_body)

    return cls


# Helper for pconfig
def _set_helpful_pconfig_init_signature_(cls: Type, _pconfig_init: Callable, original_init: Callable):
    """This makes inspect.signature() produce a helpful output. The actual signature for _pconfig_init is
    *args, **kwargs, and strict signature enforcement doesn't happen until the _pconfig_init() calls the original init()
    """
    orig_sig = inspect.signature(original_init)

    # Keep return annotation from original init
    return_anno = orig_sig.return_annotation

    new_params = [
        inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        inspect.Parameter(
            "parents",
            inspect.Parameter.VAR_POSITIONAL,
            annotation=f"{cls.__qualname__} | Ancestor[{cls.__qualname__}]",
        ),
    ]

    for p in orig_sig.parameters.values():
        if p.name == "self":
            continue

        new_param = inspect.Parameter(
            name=p.name,
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=p.default,
            annotation=p.annotation,
        )
        new_params.append(new_param)

    _pconfig_init.__signature__ = inspect.Signature(parameters=new_params, return_annotation=return_anno)


def pconfig(
    _first=None,
    *,
    constructs: Type[Any] = None,
    calls: Callable = None,
    mocks: Type[Any] = None,
    inherit_constructable_type: Optional[bool] = None,
):
    """Decorator that creates a pconfig class.

    See also:
        For examples, see :ref:`examples/construction:Construction`.

    Usage patterns:

    - ``@pconfig`` or ``@pconfig()``:
      Creates a plain pconfig dataclass.

    - ``@pconfig(constructs=MyClass)``:
      Creates a pconfig that constructs a corresponding ``@pconfiged`` class of
      type ``MyClass``.

    - ``@pconfig(calls=my_function)``:
      Creates a pconfig that calls a function that uses simply typed optional
      keyword arguments to define its configuration.

    - ``@pconfig(mocks=ExternalClass)``:
      Creates a pconfig that constructs an external class that uses simply
      typed optional keyword arguments to define its configuration. Do not use
      this pattern to design your own classes—future versions of `pconfigs`
      may raise an error if you do.

    Args:
        constructs (type, optional): A class that the pconfig should construct.
        calls (Callable, optional): A function that the pconfig should call.
        mocks (type, optional): An external class that the pconfig should construct using simply-typed keyword arguments.
        inherit_constructable_type (bool, optional): If True, the pconfig will
            inherit the constructable type of ``constructs``, ``calls``, or
            ``mocks``.

    Note:
        Exactly one of ``constructs``, ``calls``, or ``mocks`` should be provided. Supplying more than one is an error.

    Raises:
        ValueError: If more than one of ``constructs``, ``calls``, or ``mocks`` is provided.
    """
    stub = True
    legacy_mode = False
    legacy_stub = None
    dataclass_kwargs = {}

    # Ensure dataclasses do not override Config.__repr__ unless the user explicitly requests it
    dataclass_kwargs = dict(dataclass_kwargs)
    dataclass_kwargs.setdefault("repr", False)

    if legacy_mode:

        def _as_dataclass(cls):
            return dataclass(**dataclass_kwargs)(cls)

        return _as_dataclass if _first is None else _as_dataclass(_first)

    def wrap(cls, *, _callable=None):
        _validate_constructable_class(cls, _callable)

        if _callable is not None and _is_function_like(_callable) and cls.__bases__ != (object,):
            raise TypeError(
                f"@pconfig(calls=...): {cls.__name__} must not inherit from "
                f"any base class. Got bases: {', '.join(b.__name__ for b in cls.__bases__)}."
            )

        cls = _ensure_pconfig_inheritance(cls)
        cls = _normalize_environment_annotations(cls)
        cls = _validate_no_instance_defaults(cls)

        if _callable is not None:
            cls = _ensure_constructable_inheritance(cls, _callable)

            if _callable.__kwarg_mock__ not in (KwargMockType.Null, KwargMockType.Function):
                # For kwarg-mocked classes, augment the annotations with the class' __init__ params.
                if _callable.__kwarg_mock__ is KwargMockType.External:
                    func = _callable.__init__
                elif _callable.__kwarg_mock__ is KwargMockType.Derived:
                    func = _callable.__original_init__
                else:
                    raise ValueError(f"Unhandled kwarg mock type: {_callable.__kwarg_mock__.__name__}")

                _augment_annotations_from_constructable_init(cls, func=func, type_name=_callable.__name__)

            elif inspect.isfunction(_callable) or inspect.ismethod(_callable):
                _augment_annotations_from_constructable_init(cls, func=_callable, type_name=_callable.__name__)

        should_stub = stub and _class_needs_stubbing(cls) or legacy_stub is not None
        if should_stub:
            NewCls = dataclass_stubbed(cls, legacy_stub, dataclass_kwargs)
        else:
            NewCls = dataclass(**dataclass_kwargs)(cls)

        if hasattr(NewCls, "__is_pconfig_stub__") and legacy_stub is None:
            # If we are stubbed in the new system, then the original __init__ method is on the stubbed ancestor class.
            for AncestorCls in NewCls.mro():
                if getattr(AncestorCls, "__is_pconfig_stub__", None) is True:
                    original_init = AncestorCls.__init__
                    break
        else:
            # If we aren't stubbed, then the __init__ is just the top level __init__. If we are wrapping a legacy config
            # that did manual stubbing at some point, then the top-level init is still the right init.
            original_init = NewCls.__init__

        @wraps(original_init)
        def _pconfig_init(self, *args, **kwargs):
            target_cls = type(self)
            parents = []
            others = []
            for arg in args:
                if issubclass(type(arg), target_cls) and type(arg) is not target_cls:
                    msg = (
                        f"Config class '{target_cls.__name__}' is being initialized with default values from a child "
                        f"config class, '{type(arg).__name__}'. This is not supported. You can only initialize configs "
                        f"with default values from configs that are ancestor types (or other instances of themselves). "
                        f"If you are trying to initalize a derived config that inherits a pproperty, that property "
                        f"function may need to be updated to construct the derived type '{type(arg).__name__}' rather "
                        f"than the base type '{target_cls.__name__}'. "
                    )
                    raise ValueError(msg)

                if issubclass(target_cls, type(arg)):
                    parents.append(arg)
                elif (
                    getattr(target_cls, "autocopy_shared_ancestors", False)
                    and target_cls.shared_ancestor(type(arg)) is not None
                ):
                    parents.append(arg)
                else:
                    others.append(arg)

            if bool(parents) and others:
                raise NameError(
                    (
                        "Config classes cannot be initialized with unnamed arguments that are a mixture of ancestor and "
                        "non-ancestor types. \n"
                        "  Config( ancestor, c=3) : OK (canonical usage) \n"
                        "  Config( ancestor,   3) : NOT OK\n"
                        "  Config(    other,   3) : OK \n"
                        "  Config(*args, *kwargs) : OK if all *args are non-ancestor types. \n"
                    )
                )

            # Always consider the class' default config last to fill unspecified fields
            if target_cls.default_config is not None:
                parents.append(target_cls.default_config)
            else:
                # This code path is supported primarily to facilitate the user setting default configs. It doesn't seem
                # ideal for them to always rely on auto-copying from all of the defaults in the mro every time they
                # want to construct one of their configs by using defaults. They should set a default with pdefaults.
                ancestor_default_configs = [
                    cls.default_config
                    for cls in target_cls.mro()[1:]
                    if hasattr(cls, "default_config") and cls.default_config is not None
                ]
                parents.extend(ancestor_default_configs)

            # Merge fields from parents into kwargs unless explicitly provided
            our_fields_excluding_classvars = [f.name for f in get_fields_memoized(target_cls)]
            for arg in parents:
                arg = arg.inputs
                for key, val in arg.subset().items():
                    if key not in kwargs and key in our_fields_excluding_classvars:
                        kwargs[key] = val

            _conditionally_warn_about_missing_pconfiged_decorator(self, others, kwargs)

            try:
                original_init(self, *others, **kwargs)
            except TypeError as e:
                if "got multiple values for argument" in str(e):
                    non_configs = [other for other in others if not isinstance(other, PConfig)]
                    if len(non_configs) > 0:
                        non_config_types = [type(other).__name__ for other in non_configs]
                        msg = (
                            f"Config class {target_cls.__name__} is being initialized with non-config objects of types: "
                            f"{', '.join(non_config_types)}. This causes auto-copy to fail. Please only pass configs."
                        )
                        raise ValueError(msg)

                    msg = (
                        f"Config class {target_cls.__name__} is being initialized with multiple values for the same "
                        f"argument. This typically happens when you try to auto-copy parameters from an unrelated "
                        f"config (in this case, into {target_cls.__name__}). "
                    )
                    other_configs = [f"{type(other).__name__}" for other in others if isinstance(other, PConfig)]
                    if other_configs:
                        msg += (
                            f"The following positional arguments are configs that were considered for auto-copy, but "
                            f"weren't recognized as ancestors of {target_cls.__name__}: {', '.join(other_configs)}. "
                        )

                    msg += f"The original error message follows: {e}\n\n"

                    raise ValueError(msg) from e

                raise e

        # Expose a helpful signature: (self, *parents, <original params as kw-only>, **kwargs)
        _set_helpful_pconfig_init_signature_(NewCls, _pconfig_init, original_init)

        if _callable is not None:
            if not _is_function_like(_callable):
                NewCls.constructable_type = _callable
            else:
                NewCls.funcname = _callable

            if (
                inspect.isfunction(_callable)
                or inspect.ismethod(_callable)
                or _callable.__kwarg_mock__ not in (KwargMockType.Null, KwargMockType.Function)
            ):
                # Ver. 1 makes kwarg-mock constructable configs' .construct() method pass the config to the constructor.
                # Ver. 1 modernizes KwargMockFunc's __call__() method (TBD)
                if not (inspect.isfunction(_callable) or inspect.ismethod(_callable)):
                    config_version_lookup = {
                        KwargMockType.Null: 0,
                        KwargMockType.External: 0,
                        KwargMockType.Derived: 1,
                        # KwargMockType.Function: 0,  <-- Should never occur in this code path, so leaving it to throw.
                    }
                    NewCls.config_version = config_version_lookup[_callable.__kwarg_mock__]

                # Auto-create a default config instance from the original __init__ defaults.
                if getattr(NewCls, "default_config", None) is None:
                    if inspect.isfunction(_callable) or inspect.ismethod(_callable):
                        func = _callable
                    else:
                        func = getattr(_callable, "__original_init__", None) or getattr(_callable, "__init__")

                    sig = inspect.signature(func)

                    # Collect defaults from constructor signature
                    init_defaults = {}
                    for param in sig.parameters.values():
                        if param.name == "self":
                            continue
                        if param.default is inspect.Signature.empty:
                            init_defaults[param.name] = Required
                        else:
                            init_defaults[param.name] = param.default

                    # Prepare defaults for all fields declared on the config dataclass
                    new_cls_hints = get_type_hints(NewCls)
                    default_kwargs = {}
                    for f in get_fields_memoized(NewCls):
                        # Users are allowed to mark fields in the function parameters as being Pinned. If/when they do
                        # so, we need to go along with that decision as we set the defaults.
                        hint = new_cls_hints.get(f.name)
                        is_pinned = get_origin(hint) is Pinned
                        if is_pinned and f.name in init_defaults:
                            default_value = Pin(init_defaults.get(f.name))
                        elif is_pinned and f.name not in init_defaults:
                            default_value = Pinned
                        else:
                            default_value = init_defaults.get(f.name, Required)

                        default_kwargs[f.name] = default_value

                    default_instance = NewCls(**default_kwargs)
                    # Use __iadd__ in this nested scope because using "+="" makes python think pdefaults is not set yet.
                    # This also allows us to set auto_generated=True, which allows the user to override if if they wish.
                    pdefaults.__iadd__(default_instance, auto_generated=True)

        elif hasattr(NewCls, "constructable_type"):
            if inherit_constructable_type is True:
                # keep inherited constructable_type
                pass
            elif inherit_constructable_type is False:
                # Explicitly clear constructable binding for this class and make construct() produce an error
                NewCls.constructable_type = None

                def _no_construct(self):
                    raise TypeError(
                        f"{type(self).__name__} has no constructable_type bound. "
                        "Use @pconfig(YourType) or @pconfig(inherit_constructable_type=True)."
                    )

                NewCls.construct = _no_construct

            elif inherit_constructable_type is None:
                msg = (
                    f"@pconfig: {NewCls.__name__}.constructable_type = {NewCls.constructable_type.__name__}, but you "
                    f"did not specify this when decorating {NewCls.__name__} with @pconfig. Did you "
                    "forget to specify something? If you intend to inherit a constructable type, please use "
                    "@pconfig(inherit_constructable_type=True)."
                )
                raise ValueError(msg)
            else:
                raise ValueError(f"Unhandled value for inherit_constructable_type: {inherit_constructable_type}")

        # Override the default_config (a class property) if it is inherited from a parent class.
        if hasattr(NewCls, "default_config") and not isinstance(NewCls.default_config, NewCls):
            NewCls.default_config = None

        NewCls.__init__ = _pconfig_init
        NewCls.use_legacy_new_operator = False

        _throw_on_circular_property_dependencies(NewCls)

        return NewCls

    # Invocation handling:
    # - @pconfig -> _first is the class; return wrap(_first)
    # - @pconfig() -> _first is None; return wrap
    # - @pconfig(constructs=Type) or @pconfig(calls=func) -> return decorator factory
    if constructs is not None or calls is not None or mocks is not None:
        checks = [x is not None for x in [constructs, calls, mocks]]
        if sum(checks) > 1:
            raise TypeError("@pconfig: The parameters 'constructs', 'calls', and 'mocks' are mutually exclusive.")

        if constructs is not None and not hasattr(constructs, "__is_pconfiged__"):
            raise TypeError(f"@pconfig: '{constructs.__name__}' is not a @pconfiged class.")

        _callable = constructs or calls or mocks
        if mocks is not None:
            setattr(_callable, "__is_pconfiged__", bool(True))
            if not hasattr(_callable, "__kwarg_mock__"):
                setattr(_callable, "__kwarg_mock__", KwargMockType.External)

        elif calls is not None:
            # You can't set attributes on class methods (staticmethod and classmethod), but if you set them on
            # _callable.__func__, you can get the attribute directly from _callable. So, we can guarantee that all
            # _callables will return a value for the __kwarg_mock__ attribute.
            func = getattr(_callable, "__func__", _callable)
            setattr(func, "__kwarg_mock__", KwargMockType.Function)

        def _decorator(cls):
            return wrap(cls, _callable=_callable)

        return _decorator

    if _first is None:
        return wrap

    return wrap(_first)


def pproperty(_func=None, *, deps: Union[List[str], str] = None, manual_deps: bool = False):
    """Decorator that defines a computed property in a pconfig class.

    See also:
        For examples, see :ref:`examples/properties:Properties`.

    Unlike regular properties (which should be avoided), ``pproperty``-based properties have the following characteristics:

    * They are evaluated at class construction time, which enables ``python -m pconfigs.test``.
    * Their dependencies are inferred and cycles are detected at class definition time.
    * The user can provide input values to the property, which can be revised by the property.

    Usage:
        ``@pproperty`` or ``@pproperty()``

    Args:
        manual_deps (bool, optional): When ``False``, property dependencies are
            inferred from the property's source code. When ``True``, only the
            dependencies specified in ``deps`` are used.
        deps (Sequence[str], optional): Explicit list of attribute names that
            the property depends on. This is optional and should rarely be used.

    Raises:
        SyntaxError: If the property function cannot be parsed.
    """
    legacy_mode = False

    def _infer_attribute_dependencies(property_func) -> set[str]:
        names: set[str] = set()

        try:
            src = inspect.getsource(property_func)
        except (OSError, TypeError):
            return []

        try:
            import textwrap

            tree = ast.parse(textwrap.dedent(src))
        except SyntaxError:
            return []

        params = list(inspect.signature(property_func).parameters.keys())
        self_param = params[0] if params else None
        if not self_param:
            return []

        class Finder(ast.NodeVisitor):
            def __init__(self):
                self.func_depth = 0

            def visit_FunctionDef(self, node):
                self.func_depth += 1
                if self.func_depth == 1:
                    self.generic_visit(node)
                self.func_depth -= 1

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Lambda(self, node):
                # Don't traverse into lambda functions
                return

            def visit_Attribute(self, node):
                # This is the main case where we catch references like self.x and self.x.y are both accessing self.x
                try:
                    if (
                        isinstance(node.value, ast.Name)
                        and node.value.id == self_param
                        and isinstance(node.ctx, ast.Load)
                    ):
                        names.add(node.attr)
                finally:
                    self.generic_visit(node)

            def visit_Call(self, node):
                # Handle getattr(self, "x") cases where "x" is a string literal. We cannot execute the code for them,
                # but catching this and the basic self.x references are going to handle 99% of good practice use cases.
                try:
                    if (
                        isinstance(node.func, ast.Name)
                        and node.func.id == "getattr"
                        and len(node.args) >= 2
                        and isinstance(node.args[0], ast.Name)
                        and node.args[0].id == self_param
                        and isinstance(node.args[1], ast.Constant)
                        and isinstance(node.args[1].value, str)
                    ):
                        names.add(node.args[1].value)
                finally:
                    self.generic_visit(node)

        Finder().visit(tree)

        return names

    prop_inputs_obj = PinnableConfig.PropInputs(deps=deps)

    def _decorate(property_func):
        prop = property(property_func)
        if legacy_mode:
            return prop_inputs_obj(prop)

        deps_inferred = _infer_attribute_dependencies(property_func)
        if isinstance(deps, str):
            deps_user = {deps}
        elif deps is None:
            deps_user = set()
        else:
            deps_user = set(deps)

        if manual_deps:
            deps_all = deps_user
        else:
            deps_all = deps_inferred | deps_user

        if property_func.__name__ in deps_all:
            msg = (
                f"@pproperty: {property_func.__name__} cannot access itself. This is an infinite loop. Use "
                f"pinputs(self).{property_func.__name__} to access user-input values."
            )
            raise ValueError(msg)

        if not deps_all:
            deps_all = None

        return PinnableConfig.PropInputs(deps=deps_all)(prop)

    if _func is None:
        return _decorate

    return _decorate(_func)


T = TypeVar("T")


class PEnum(Enum):
    def __repr__(self):
        return f"{self.__class__.__name__}.{self._name_}"

    @classmethod
    def make(cls: Type[T], value: str) -> T:
        for tag in cls:
            if tag.value == value:
                return tag

        raise ValueError(f"Enum value '{value}' is not defined by {cls.__name__}")


def penum(cls):
    if issubclass(cls, PEnum):
        return cls

    def exec_body(ns):
        ns["__module__"] = cls.__module__
        ns["__qualname__"] = cls.__qualname__
        ns["__doc__"] = cls.__doc__
        for key, val in cls.__dict__.items():
            if key in ("__dict__", "__weakref__", "__annotations__", "__module__", "__doc__", "__qualname__"):
                continue
            ns[key] = val

    return types.new_class(cls.__name__, (PEnum,), {}, exec_body)


@pconfig
class IdentifiablePConfig:
    @property
    def identifier(self) -> str:
        """Dataclasses natively support hashing, but they don't tolerate non-hashable fields like lists."""
        cereal = ""
        for value in self.identifiable_values:
            if isinstance(value, IdentifiablePConfig):
                cereal += value.identifier
            else:
                cereal += repr(value)

        identifier = hashlib.sha256(cereal.encode("utf-8")).hexdigest()

        return identifier

    @property
    def identifiable_values(self) -> List[Any]:
        return [getattr(self, field.name) for field in fields(self)]


def pconfiged(_cls=None, *, runnable: bool = False, mock: bool = False):
    """Decorator that creates a pconfiged object.

    See also:
        For examples, see :ref:`examples/construction:Construction`.

    When used with keyword options, it behaves as follows.

    Args:
        runnable (bool, optional): If True, the class can be run with
            ``python -m pconfigs.run dot.path.to.config``, where the dot‑path
            specifies an object within a Python module. The class will expose a
            ``main`` method with signature
            ``def main(self, args: Namespace, others: List[str]) -> int``.
            The ``args`` parameter will have a single value, ``args.config``,
            which is the dot-path of the config (for example, ``dot.path.to.config``).
            See ``pconfigs.config_runner.ConfigRunnable`` for more details.
        mock (bool, optional): If True, the pconfiged class may come from an
            external library that uses simple, keyword-only arguments to define
            its configuration.
    """

    def _decorate(cls):
        target_cls = cls

        # Optionally inject ConfigRunnable into the class hierarchy
        if runnable:
            from pconfigs.config_runner import ConfigRunnable

            if not issubclass(target_cls, ConfigRunnable):

                def exec_body(ns):
                    ns["__module__"] = target_cls.__module__
                    ns["__qualname__"] = target_cls.__qualname__
                    ns["__doc__"] = target_cls.__doc__
                    # Preserve annotations so the 'config' annotation remains visible
                    ns["__annotations__"] = dict(getattr(target_cls, "__annotations__", {}))
                    for key, val in target_cls.__dict__.items():
                        if key in (
                            "__dict__",
                            "__weakref__",
                            "__annotations__",
                            "__module__",
                            "__doc__",
                            "__qualname__",
                        ):
                            continue
                        ns[key] = val

                # Keep original class first in MRO; add ConfigRunnable as mixin
                target_cls = types.new_class(target_cls.__name__, (target_cls, ConfigRunnable), {}, exec_body)

        # Resolve annotation name without requiring the target type to be defined yet
        annotations = getattr(target_cls, "__annotations__", {})
        if "config" not in annotations:
            raise TypeError(f"@pconfiged requires an annotation 'config: <ConfigType>' in {target_cls.__name__}")

        # Patch __init__: accept config and chain to original __init__ (unless it is a
        # pconfiged-generated init from a parent class, in which case we skip to avoid
        # double-handling the config argument). If an existing non-pconfiged __init__ already
        # accepts a 'config' parameter, raise to avoid ambiguous behavior.

        target_init = getattr(target_cls, "__init__", None)
        original_init = target_init
        if callable(target_init) and getattr(target_init, "__is_pconfiged__", False):
            original_init = None

        elif callable(target_init) and target_init is not object.__init__:
            sig = inspect.signature(target_init)
            params_beyond_self = [p for p in sig.parameters.values() if p.name != "self"]
            if params_beyond_self and not mock:
                msg = (
                    f"@pconfiged: {target_cls.__name__}.__init__ shall not declare parameters. Got signature:\n  "
                    f"{target_cls.__name__}.__init__{sig}"
                )
                raise TypeError(msg)

        annotated_config_name = annotations["config"]

        def _pconfig_init(self, *args, config=None, **kwargs):
            # Allow user to call super().__init__() without passing the invisible config parameter.
            if config is None:
                if "config" not in self.__dict__:
                    self_name = type(self).__name__
                    msg = (
                        f"@pconfiged: class '{self_name}' must be constructed with a 'config' argument. "
                        f"Are you trying to directly construct '{self_name}' without using the associated config class, "
                        f"'{annotated_config_name}'?"
                    )
                    raise TypeError(msg)

                config = self.__dict__["config"]

            self.config = config
            if original_init is not None and original_init is not object.__init__:
                original_init(self, *args, **kwargs)

        # Mark this as our pconfiged init function.
        setattr(_pconfig_init, "__is_pconfiged__", True)

        if getattr(target_init, "__is_pconfiged__", False):
            _pconfig_init = target_init

        if original_init is not None and original_init is not object.__init__:
            setattr(target_cls, "__original_init__", original_init)

        setattr(target_cls, "__init__", _pconfig_init)
        setattr(target_cls, "__is_pconfiged__", True)
        setattr(target_cls, "__kwarg_mock__", KwargMockType.Null if not mock else KwargMockType.Derived)

        return target_cls

    # Support both @pconfiged and @pconfiged(...)
    if _cls is None:
        return _decorate
    else:
        return _decorate(_cls)


ConventionTransform = Callable[[str], str]
Convention = Union[Literal["uppercase"], Callable[[str], str]]


def penv(
    _cls=None,
    *,
    convention: Union[Convention, ConventionTransform] = None,
):
    """Decorator that creates a config that accesses environment variables.

    See also:
        For examples, see :ref:`examples/environments:Environments`

    The decorator can be used with or without arguments:

    * ``@penv`` or ``@penv()``: Use the attribute name as the environment
      variable name.
    * ``@penv(convention="uppercase")``: Convert attribute names to uppercase
      when deriving environment variable names (for example, ``my_flag`` →
      ``MY_FLAG``).
    * ``@penv(convention=callable)``: Use a custom callable
      ``convention(name: str) -> str`` to transform attribute names into environment variable names.

    Args:
        convention (Convention | ConventionTransform, optional): Name
            transformation strategy for environment variable names. May be the
            string ``"uppercase"`` or a callable ``(str) -> str``. If omitted,
            attribute names are used as is.

    Returns:
        :class:`Type`: A new class derived from :class:`EnvironmentBase` and using
        :class:`EnvironmentMetaclass`, with annotated attributes replaced by :class:`EnvVar` descriptors.

    Raises:
        ValueError: If an unsupported string convention is provided.
    """
    from pconfigs.environment import EnvironmentBase, EnvironmentMetaclass, EnvVar, NoDefault

    def transform_name(name: str) -> str:
        if callable(convention):
            return convention(name)
        if isinstance(convention, str):
            tag = convention.lower()
            if tag == "uppercase":
                return name.upper()
            raise ValueError(f"@penv: unsupported convention '{convention}'")

        return name

    def decorate(cls):
        def exec_body(ns):
            ns["__module__"] = cls.__module__
            ns["__qualname__"] = cls.__qualname__
            ns["__doc__"] = cls.__doc__
            # Preserve annotations so type hints continue to work
            annotations = dict(getattr(cls, "__annotations__", {}))
            ns["__annotations__"] = annotations

            # Copy all original attributes, but convert annotated plain defaults to EnvVar
            for key, val in cls.__dict__.items():
                if key in ("__dict__", "__weakref__", "__annotations__", "__module__", "__doc__", "__qualname__"):
                    continue

                if key in annotations:
                    if isinstance(val, EnvVar):
                        ns[key] = val
                    else:
                        ns[key] = EnvVar(transform_name(key), val)
                else:
                    ns[key] = val

            # Ensure every annotated field exists as an EnvVar (even if no default was given)
            for key in annotations.keys():
                if key not in ns:
                    ns[key] = EnvVar(transform_name(key), NoDefault)

        # Ensure the class derives from EnvironmentBase exactly once
        if issubclass(cls, EnvironmentBase):
            bases = cls.__bases__
        else:
            bases = (EnvironmentBase,) + cls.__bases__

        # Recreate the class with the EnvironmentMetaclass and updated bases
        return types.new_class(cls.__name__, bases, {"metaclass": EnvironmentMetaclass}, exec_body)

    if _cls is None:
        return decorate
    else:
        return decorate(_cls)


CT = TypeVar("CT", bound=PConfig)


class PSetter(Generic[CT]):
    if TYPE_CHECKING:

        @overload
        def __new__(cls, type: Type[CT], inputs: CT | None = ..., parent: Any = ...) -> CT: ...

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, type: Type[CT], inputs: CT | None = None, parent: PSetter[Any] | None = None):
        self.__type = type
        self.__parent = parent
        self.__inputs = inputs
        self.__values = {}
        self.__active = False
        if inputs is not None and not isinstance(inputs, type):
            raise ValueError(f"Inputs is of type {type(inputs).__name__}, which doesn't match {type.__name__}.")

    def __enter__(self) -> CT:
        self.__active = True
        return cast(CT, self)

    def __exit__(self, exc_type, exc, tb) -> None:
        self.__active = False
        return False

    def _is_active(self) -> bool:
        if self.__active:
            return True
        if self.__parent is not None:
            return self.__parent._is_active()

        return False

    def _ensure_active(self) -> None:
        if not self._is_active():
            raise RuntimeError("PSetter must be used inside a 'with' block on the root instance")

    @property
    def _class_dotpath(self) -> str:
        if self.__parent is None:
            return self.__type.__name__

        return f"{self.__parent._class_dotpath}.{self.__type.__name__}"

    @property
    def pconfig(self) -> CT:
        # self._ensure_active()
        resolved_values = {
            name: value.pconfig if isinstance(value, PSetter) else value for name, value in self.__values.items()
        }
        type = self.__type if self.__inputs is None else self.__inputs.__class__
        if self.__inputs is not None:
            config = type(self.__inputs, **resolved_values)
        else:
            config = type(**resolved_values)

        return config

    def _get_subconfig_types(self, field_type: Any) -> List[Type[PConfig]]:
        from pconfigs.kwarg_mock import NotMock
        while True:
            origin = get_origin(field_type)
            if origin in (Pinned, NotMock):
                args = get_args(field_type)
                if not args:
                    return []

                field_type = args[0]
                continue

            if origin in (Union, types.UnionType):
                args = get_args(field_type)
                args_non_none = [arg for arg in args if arg is not type(None)]

                if len(args_non_none) == 1:
                    # Recursive base case: only one subconfig type
                    field_type = args_non_none[0]
                    continue

                subconfig_types = []
                for arg in args_non_none:
                    subconfig_types.extend(self._get_subconfig_types(arg))

                return subconfig_types

            if isinstance(field_type, type) and issubclass(field_type, PConfig):
                # Base case: found a single subconfig type
                return [field_type]

        raise ValueError(f"Unexpected error. Execution should not reach this point. Got field type: {field_type!r}")

    def __getattr__(self, name: str) -> Any:
        # self._ensure_active()
        vals = object.__getattribute__(self, "_PSetter__values")
        if name in vals:
            return vals[name]

        type = object.__getattribute__(self, "_PSetter__type")
        hints = get_type_hints_memoized(type)
        subtype = hints.get(name, None)
        if subtype is None:
            raise AttributeError(f"Attribute {name} is not an attribute of type {type.__name__}")

        subconfig_types = self._get_subconfig_types(subtype)
        if len(subconfig_types) > 1:
            raise ValueError(f"Attribute {name} has multiple subconfig types: {subconfig_types}. Cannot infer intended type.")

        elif len(subconfig_types) == 0:
            raise AttributeError(f"Attribute {name} is not a subconfig of {type.__name__}")

        subtype = subconfig_types[0]
        if issubclass(subtype, PConfig):
            inputs = object.__getattribute__(self, "_PSetter__inputs")
            subinputs = getattr(inputs, name, None)
            if subinputs is not None:
                if not issubclass(subinputs.__class__, subtype):
                    raise ValueError(
                        f"Inputs attribute {self._class_dotpath}.{name} is of type {subinputs.__class__.__name__}, which "
                        f"doesn't match the expected type {subtype.__name__}."
                    )

                subtype = subinputs.__class__

            value = PSetter(
                type=subtype,
                inputs=subinputs,
                parent=self,
            )
            self.__values[name] = value
            return value

        raise AttributeError(f"Attribute {name} is not a subconfig of {type.__name__}")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith(f"_{self.__class__.__name__}__"):
            object.__setattr__(self, name, value)
        else:
            # self._ensure_active()
            if name in self.__values:
                raise ValueError(f"Attribute {self._class_dotpath}.{name} is already set")

            self.__values[name] = value


@overload
def psetter(*, construct: PSetter[CT]) -> CT: ...


@overload
def psetter(*, type: Type[CT], inputs: CT | None = ...) -> CT: ...


def psetter(*, construct: PSetter[CT] | None = None, type: Type[CT] | None = None, inputs: Any = None) -> Any:
    """Helper for constructing pconfig instances.

    See also:
        For examples, see :ref:`Make short property functions with psetter <subsec-make-short-property-functions-with-psetter>`.

    This function has two keyword-only modes of operation:

    1. ``psetter(type=MyConfig, inputs=...)``: Given a pconfig class and
       an optional inputs, return a :class:`PSetter` view that can be used
       to succintly set config values that are deeply nested within sub-configs of the config.
    2. ``psetter(construct=...)``: Given an existing :class:`PSetter` instance,
       return the fully constructed config object it represents.

    Args:
        construct (PSetter, keyword-only): An existing
            :class:`PSetter` instance to be materialized into its underlying
            config. Must not be combined with ``type`` or ``inputs``.
        type (Type[CT] | None, keyword-only): A pconfig class for which a
            :class:`PSetter` view should be created. Must not be combined with
            ``construct``.
        inputs (Any, optional, keyword-only): Optional initial inputs for the
            created :class:`PSetter` when using the ``type=...`` form.

    Returns:
        Type | PSetter[Type]: Either the constructed config instance (when
        ``construct`` is provided) or a :class:`PSetter` view (when ``type`` and ``inputs`` are provided).

    Raises:
        TypeError: If incompatible combinations of arguments are provided
            (for example, both ``construct`` and ``type``), or if neither ``construct`` nor ``type`` is given.
    """
    if construct is not None:
        if type is not None or inputs is not None:
            raise TypeError("psetter: 'construct' cannot be combined with 'type' or 'inputs'")
        return cast(CT, construct.pconfig)

    if type is not None:
        if construct is not None:
            raise TypeError("psetter: 'type' cannot be combined with 'construct'")
        ps = PSetter(type, inputs)
        return cast(CT, ps)

    raise TypeError("psetter: expected either 'construct=' or 'type=' keyword")
