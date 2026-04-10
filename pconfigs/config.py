# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any, Callable, ClassVar, Dict, List, Optional, Type, Union, get_args, get_origin, get_type_hints

try:
    import black
except:
    pass

try:
    from typing import Protocol
except ImportError:  # Python <3.8 fallback
    from typing_extensions import Protocol

from pconfigs.environment import EnvironmentMetaclass
from pconfigs.iterators import markfirst


class MemoizedCall:
    def __init__(self, func):
        self.func = func
        self.memo = {}

    def __call__(self, entry: Any):
        if entry not in self.memo:
            self.memo[entry] = self.func(entry)

        return self.memo[entry]


get_fields_memoized = MemoizedCall(fields)


class DataClassType(Protocol):
    # dataclass is not a type. The proper way to check if something is a dataclass via the type hint idiom is to specify
    # a protocol (cf. stackoverflow link). The protocol checks for an attribute that is specific to dataclasses, which
    # again according to stackoverflow is currently the most reliable way to ascertain that something is a dataclass.
    # And anyway, it is wholly appropriate for our use, which is to require the presence of the dataclass fields dict.
    # https://stackoverflow.com/questions/54668000/type-hint-for-an-instance-of-a-non-specific-dataclass
    __dataclass_fields__: Dict


class CastableDataclass:
    def downcast(self, subtype: DataClassType) -> DataClassType:
        subclass = subtype(**{key: getattr(self, key) for key in subtype.__dataclass_fields__.keys()})
        return subclass


class ImportsBuilder:
    def __init__(self):
        self.imports = {}

    def non_colliding_add(self, typename: str, module: str) -> str:
        typename_init = typename
        typename_suffix = 2
        while typename in self.imports and self.imports[typename] != module:
            typename = (typename_init, typename_suffix)
            typename_suffix += 1

        if typename not in self.imports:
            self.imports[typename] = module

        return self.format_name(typename)

    def format_name(self, name: str | tuple) -> str:
        if isinstance(name, str):
            return name
        elif isinstance(name, tuple):
            return f"{name[0]}_v{name[1]}"
        else:
            raise ValueError(f"Name type is not handled: {type(name)}.")

    def __str__(self):
        imports_collated = defaultdict(list)
        for name, module in self.imports.items():
            imports_collated[module].append(name)

        imports = []
        for module, names in imports_collated.items():
            imports_direct = []
            imports_rename = []
            for name in names:
                if isinstance(name, str):
                    imports_direct.append(name)
                elif isinstance(name, tuple):
                    imports_rename.append(name)

            if imports_direct:
                imports += [f"from {module} import {', '.join(imports_direct)}"]

            for name_tuple in imports_rename:
                old_name = name_tuple[0]
                new_name = self.format_name(name_tuple)
                imports += [f"from {module} import {old_name} as {new_name}"]

        return "\n".join(imports)


def issubclass_legacy_compat(value: Type, type: Type) -> bool:
    if value.__name__ == type.__name__:
        # This handles EnvironmentMetaclass types, which don't have a mro() method. If you call type(thing), where
        # thing is created with @penv, then you get type(thing) == EnvironmentMetaclass. This is a special case.
        return True

    type_name = type.__name__
    try:
        result = any(t.__name__ == type_name for t in value.mro())
    except TypeError as e:
        if "unbound method type.mro() needs an argument" not in str(e):
            raise e

        result = False

    return result


@dataclass
class PrettyPrinterDataclass:
    def _sanitize_printed_value(self, string: str) -> str:
        # Remove class names from strings like <class 'something'>
        string = re.sub(r"<class\s+'([^']*)'>", r"\1", string)

        # From strings like <something.other: value>, keep `something.other`.
        # Examples:
        #   <JunkEnum.First: 'first'> -> JunkEnum.First
        #   <SomeType.value: 2>      -> SomeType.value
        string = re.sub(r"<\s*([^<>\s:>]+\.[^<>\s:>]+)\s*:\s*[^>]+>", r"\1", string)

        return string

    def skip_print_key(self, key: str) -> bool:
        return False

    def print_code(self, shortnames=True) -> str:
        imports = ImportsBuilder()
        config_str = self._print(prefix=None, trace=False, shortnames=shortnames, imports=imports)

        warning = (
            "\n\n# NOTE: This code is not intended to run. It is for reading and looking up type definitions.\n"
            "# If you want to run or inspect these objects, import the config from where it is defined."
        )

        result = "{}{}\n\n{})".format(imports, warning, config_str)
        try:
            result = black.format_str(result, mode=black.Mode())
        except:
            pass

        return result

    def _print(self, prefix=None, trace=False, shortnames=True, imports: ImportsBuilder = None):
        if not trace:
            field_lens = self._print(prefix, trace=True)
            max_field_len = 0 if not field_lens else max(field_lens)
            field_fmt = "{:" + str(max_field_len) + "}"

        base_prefix = " "
        if trace:
            prefix = base_prefix if prefix is None else prefix
            ans = []
        elif prefix is None:
            prefix = base_prefix
            typename = type(self).__name__ if shortnames else str(type(self))
            if imports is not None:
                typename = imports.non_colliding_add(typename, self.__class__.__module__)

            ans = typename + "(\n"
        else:
            ans = ""

        try:
            typehints = get_type_hints(type(self))
        except NameError as e:
            import inspect

            filepath = inspect.getfile(type(self))
            msg = f"Could not get typehints for {type(self).__name__}: {e}. The issue comes from here: {filepath}"
            raise NameError(msg)

        for key in typehints.keys():
            if self.skip_print_key(key):
                continue

            # Bad coding. The pinnable classes should be responsible for changing how printing happens
            # But, the whole system is going to be rewritten, so for now we do a text-based strategy of omitting pinned
            # fields if we are printing with imports for re-implementation.
            typehint = typehints[key]
            is_pinned = hasattr(self, "_is_pinned") and self._is_pinned(typehint)
            is_classvar = hasattr(typehint, "__origin__") and typehint.__origin__ == ClassVar
            is_classvar_callable = is_classvar and isinstance(typehint.__args__[0], Callable)
            if is_pinned:
                comment = "  # Pinned (omit from config)"
            elif is_classvar:
                comment = "  # ClassVar (omit from config)"
            else:
                comment = ""

            if key.endswith("_lambda"):
                key = key.split("_lambda")[0]

            if is_classvar_callable:
                # If a callable is attached as a classvar, it is intended to be called as in type(thing).field
                # Using getattr(self, key) will produce the wrong value.
                val = getattr(type(self), key)
            else:
                val = getattr(self, key)

            keystr = "{}{}".format(prefix, key)
            if issubclass_legacy_compat(type(val), Config):
                if trace:
                    ans += [len(keystr)]
                    ans += val._print(prefix + "  ", trace=True, shortnames=shortnames, imports=imports)
                else:
                    typename = type(val).__name__ if shortnames else str(type(val))
                    if imports is not None:
                        typename = imports.non_colliding_add(typename, val.__class__.__module__)

                    ans += (field_fmt + " = {}({}\n").format(keystr, typename, comment)
                    ans += val._print(prefix + "  ", trace=False, shortnames=shortnames, imports=imports)
                    ans += prefix + "),\n"

            elif issubclass(type(val), list) and any([issubclass_legacy_compat(type(x), Config) for x in val]):
                if trace:
                    ans += [len(keystr)]
                    for x in val:
                        if issubclass_legacy_compat(type(x), Config):
                            ans += x._print(prefix + "   ", trace=True, shortnames=shortnames, imports=imports)
                        else:
                            ans += (len(self._sanitize_printed_value(string=str(x))),)

                else:
                    ans += (field_fmt + " = [\n").format(keystr)
                    for index, x in enumerate(val):
                        if issubclass_legacy_compat(type(x), Config):
                            typename = type(x).__name__ if shortnames else str(type(x))
                            if imports is not None:
                                typename = imports.non_colliding_add(typename, x.__class__.__module__)

                            ans += (prefix + "  {}(\n").format(typename)
                            ans += x._print(prefix + "    ", trace=False, shortnames=shortnames, imports=imports)
                            ans += (prefix + "  ),\n").format(" " * len(keystr))
                        else:
                            x_str = self._sanitize_printed_value(string=str(x))
                            ans += prefix + "  " + x_str + ",\n"

                    ans += prefix + "],\n"

            elif issubclass(type(val), dict) and any(
                [issubclass_legacy_compat(type(val), Config) for key, val in val.items()]
            ):
                if trace:
                    ans += [len(keystr)]
                    for key, x in val.items():
                        if issubclass_legacy_compat(type(x), Config):
                            ans += x._print(prefix + "   ", trace=True, shortnames=shortnames, imports=imports)
                        else:
                            ans += (len(self._sanitize_printed_value(string=str(x))),)

                else:
                    ans += (field_fmt + " = {{\n").format(keystr)
                    for subkey, x in val.items():
                        if issubclass_legacy_compat(type(x), Config):
                            typename = type(x).__name__ if shortnames else str(type(x))
                            if imports is not None:
                                typename = imports.non_colliding_add(typename, x.__class__.__module__)

                            ans += (prefix + "  {}: {}(\n").format(subkey, typename)
                            ans += x._print(prefix + "    ", trace=False, shortnames=shortnames, imports=imports)
                            ans += (prefix + "  ),\n").format(" " * len(keystr))
                        else:
                            x_str = self._sanitize_printed_value(string=str(x))
                            ans += prefix + "  " + x_str + ",\n"

                    ans += prefix + "},\n"

            elif issubclass_legacy_compat(type(val), EnvironmentMetaclass):
                if trace:
                    ans += [len(keystr)]
                    for line in str(val).split("\n"):
                        varname = line.split("=")[0]
                        ans += [len(prefix) + len(varname)]
                else:
                    typename = val.__name__ if shortnames else f"{val.__module__}.{val.__name__}"
                    typename_safe = None
                    if imports is not None:
                        typename_safe = imports.non_colliding_add(typename, val.__module__)
                        typename_safe = None if typename_safe == typename else typename_safe

                    lines = str(val).split("\n")
                    if typename_safe is not None:
                        lines[0] = lines[0].replace(typename, typename_safe)

                    lines[0] += comment
                    lines = [v if isfirst else prefix + v for v, isfirst in markfirst(lines)]
                    val = "\n".join(lines)
                    comment = ""
                    ans += (field_fmt + " = {},{}\n").format(keystr, val, comment)

            elif trace:
                ans += [len(keystr)]

            elif not trace:
                if isinstance(val, str):
                    val = '"{}"'.format(val)
                elif callable(val) and not isinstance(val, type):
                    # If its a function, we print the dotpath to the function
                    val = f"{val.__module__}.{val.__name__}"
                elif isinstance(val, Enum):
                    typename = type(val).__name__
                    typename_orig = typename
                    if imports is not None:
                        typename = imports.non_colliding_add(typename, val.__class__.__module__)

                    if shortnames:
                        val = str(val).replace(typename_orig, typename)
                    else:
                        val = "{}.{}".format(val.__class__.__module__, val)

                elif isinstance(val, type) and shortnames:
                    typename = val.__name__
                    if imports is not None:
                        typename = imports.non_colliding_add(typename, val.__module__)

                    val = typename

                # Replace substrings like <something: 'other'> with the quoted value 'other'
                val_str = self._sanitize_printed_value(string=str(val))
                field_str = (field_fmt + " = {},{}\n").format(keystr, val_str, comment)
                ans += field_str

        return ans

    def __str__(self):
        result = self._print() + ")"
        try:
            result = black.format_str(result, mode=black.Mode())
        except:
            pass

        return result

    def __repr__(self):
        return self.print_code()


class DictGetterDataclass:
    """Dataclass that will returns a dict of its fields and values without recursing."""

    def asdict(self, use_proper_dataclass_field_getter: bool = True):
        if use_proper_dataclass_field_getter:
            # Using fields() excludes classvars from the returned attributes.
            field_dict = {f.name: getattr(self, f.name) for f in get_fields_memoized(type(self))}
        else:
            field_dict = {key: getattr(self, key) for key in self.__dataclass_fields__.keys()}

        return field_dict

    def subset(
        self,
        excludes: Optional[List[str]] = None,
        includes: Optional[List[str]] = None,
        use_proper_dataclass_field_getter: bool = True,
    ) -> Dict[Any, Any]:
        excludes = [] if excludes is None else excludes
        includes = list(self.asdict(use_proper_dataclass_field_getter).keys()) if includes is None else includes
        fields = {
            key: value
            for key, value in self.asdict(use_proper_dataclass_field_getter).items()
            if key not in excludes and key in includes
        }
        return fields


@dataclass(repr=False)
class Config(PrettyPrinterDataclass, DictGetterDataclass):
    """Simplify parameter configs. Create your dataclasses by passing *kwargs into the constructor, and
    only using *args to pass other config objects that have fields that you want to copy. For example you
    might have dataclasses
      B = Base(x=1, y=2)
      D = Derived(x=1, y=2, z=3)

    If you derive them from this Config class, you can instead do
      D = Derived(B, z=3)

    And note that your manually typed kwargs take precedence:
      D = Derived(B, x=10, z=3)
      print(D)
      >>> Derived(x=10, y=2, z=3)

    Great. Now consider 3 configs:
        A = Alpha(x=1, y=2)
        B = Beta(y=3, z=4)
        E = Epsilon(x=1, y=2, z=4, q=5)

    We want x=1 and y=2 from A, z=4 from B, and we want to set q=5 for E. Instead of repeating the values
    across config files, you can tie them together like this
        E = Epsilon(A, B, q=5)

    The parameter values in A will override those in B because A comes first. Similarly,
        E = Epsilon(B, A, q=5)
        print(E)
        >>> Epsilon(x=1, y=3, z=4, q=5)

    Lastly, you can mix and match settings using .include and .exclude operators:
        D = Delta(x=10, y=20)
        E = Epsilon(
            A.include('x'),  # sets x
            D.exclude('x'),  # sets y
            B.include('z'),
            q=5,
        )

    This will work for nested configs as well.
    """

    autocopy_shared_ancestors: ClassVar[bool] = False
    # You should not be changing this classvar yourself.
    # This must default to True so old configs that use @dataclass will default correctly work.
    # New classes should use @pconfig and that decorator will set this class property appropriately.
    use_legacy_new_operator: ClassVar[bool] = True

    def __post_init__(self):
        self._includes = None
        self._excludes = None
        # Debug info
        # cls = type(self)
        # print('-Post Init-')
        # print('Class name:   ', cls.__name__, ', ', cls._name if hasattr(cls, '_name') else 'No cls._name')
        # print('Backup init:  ', cls._initializer.__code__.co_varnames if hasattr(cls, '_initializer') else 'No cls._initializer')
        # print('Formal init:  ', cls.__init__.__code__.co_varnames)
        # print('Self:         ', self)
        # print('')

    def include(self, *field_names):
        self._includes = field_names
        return self

    def exclude(self, *field_names):
        self._excludes = field_names
        return self

    def subset(
        self,
        excludes: Optional[List[str]] = None,
        includes: Optional[List[str]] = None,
        use_proper_dataclass_field_getter: bool = True,
    ) -> Dict[Any, Any]:
        # These are set in __post_init__, but if the dataclass has no fields at all, neither init nor post_init are run
        # so we have to set them here to avoid an error. This lets users to stub out empty config classes for future use
        if not hasattr(self, "_includes"):
            self._includes = None

        if not hasattr(self, "_excludes"):
            self._excludes = None

        # The optional parameters are deprecated, and are only here to support legacy code.
        # Suggested call semantics are, config.exclude('field').subset()
        if excludes is not None or includes is not None:
            return super().subset(
                excludes, includes, use_proper_dataclass_field_getter=use_proper_dataclass_field_getter
            )

        return super().subset(
            includes=self._includes,
            excludes=self._excludes,
            use_proper_dataclass_field_getter=use_proper_dataclass_field_getter,
        )

    @classmethod
    def shared_ancestor(cls, other: Type) -> Optional[Type]:
        prefix_class_names = [
            "PConfig",
            "PinnableConfig",
            "ConstructableConfig",
            "Config",
            "PrettyPrinterDataclass",
            "DictGetterDataclass",
            "ConfigConstructableInterface",
            "ABC",
            "object",
        ]
        lineage_arg = [x.__name__ for x in other.mro() if x.__name__ not in prefix_class_names]
        lineage_cls = [x.__name__ for x in cls.mro() if x.__name__ not in prefix_class_names]
        lineage_arg = "/".join(lineage_arg[::-1])
        lineage_cls = "/".join(lineage_cls[::-1])
        shared_ancestor_name = os.path.commonpath([lineage_cls, lineage_arg]).split(os.sep)[-1]
        shared_ancestor_cls = [x for x in cls.mro() if x.__name__ == shared_ancestor_name]

        if not shared_ancestor_cls:
            return None

        return shared_ancestor_cls[-1]

    def __new__(cls, *args, **kwargs):
        """Be warned that the code in this function is extraordinarily subtle. This modifies properties of the class,
        which affects future instantiantions of the same class. That is not a good design, so its now legacy behavior.
        """
        if not getattr(cls, "use_legacy_new_operator", True):
            return super().__new__(cls)

        # From here on, the logic matches the legacy implementation
        parents = []
        others = []
        for arg in args:
            if issubclass(cls, type(arg)):
                parents.append(arg)
            elif cls.autocopy_shared_ancestors and cls.shared_ancestor(type(arg)) is not None:
                parents.append(arg)
            else:
                others.append(arg)

        if bool(parents) and others:
            # We cannot handle this case without great coding effort because the order of the dataclass __init__
            # parameters is defined by the inheritance order (MRO). Yes, we could walk that and figure it out.
            # No, its not worth the time. Config classes therefore operate like normal dataclasses unless all *args
            # are parents--only then do we permit the fancy initialization logic. When there are parents and others,
            # we throw. By the way, there is some chance that dataclasses.fields() will give us the correct order,
            # but nothing in the documentation guarantees that it will. Play it safe.
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

        # We overload the __new__ operator to re-define how python dataclasses initialize themselves.
        # This adds key initialization features that are relevant to managing configuration data classes.
        #
        # This code was inspired by the following stack overflow post
        #   https://stackoverflow.com/questions/55099243/python3-dataclass-with-kwargsasterisk
        #
        # That post solves a different problem, but you can learn from it. Below are comments to explain better.
        if not hasattr(cls, "_initializer") or cls.__name__ != cls._name:
            # The first time each derived class of type Config is constructed, we replace the default init function for
            # that class (cls.__init__) with a generic lambda that does nothing. Why? When this __new__ call completes,
            # cls.__init__ will get called by the python interpreter, so by replacing cls.__init__ with a generic lambda,
            # we prevent the dataclass init function from being called automatically. We can't allow that because the
            # automated call will be fed with the parameter list you supplied, and that will generate errors. It will
            # generate errors because we are allowing you to pass parameters in a custom manner that enables this
            # function to do some of work you would otherwise have to do yourself in order to initialize your config
            # dataclasses.
            #
            # The next key thing we do is save the cls.__init__ function to private member cls._initializer. Why? When a
            # second instance of the derived class is constructed, these private class members will still be set. Since
            # they're set, we will know that the cls.__init__ has already been replaced with a generic lambda, so we
            # should use cls._initializer to init. (Remember, setting properties on the cls is a global operation. All
            # instances of a class see the same class properties. cls.property is not the same as self.property--the
            # latter refers to an instance, the former refers to the class type itself.)
            #
            # The last key thing we do is save the class name as cls._name. If a base Config class B is constructed
            # before a Config class D that is derived from B, then cls._initializer will already be set by B when the
            # __new__ function for D runs. Class D therefore checks the cls._name, and it will see that the name is for
            # base B. D will therefore know that cls._initializer is for the base B, not itself. D will set its own
            # __init__ function, which (by the way) has not been modified by B because every class has its own __init__
            # that is independent from all ancestors or descendents.
            #
            # The only mystery behind how this class works is why constructing a base B, then derived D, then another
            # base B doesn't cause the cls.__init__ function for B to get lost. Tests show that it does not.
            cls._name = cls.__name__
            cls._initializer = cls.__init__
            cls.__init__ = lambda *a, **k: None

        initializer = cls._initializer

        # Now we have an initializer, and parents XOR others is not empty
        # Transform fields from the parents into kwargs, if those kwargs aren't already set.
        our_fields_excluding_classvars = [f.name for f in fields(cls)]
        for arg in parents:
            for key, val in arg.subset().items():
                if key not in kwargs and key in our_fields_excluding_classvars:
                    kwargs[key] = val

        ret = object.__new__(cls)
        # Debug info
        # print('-Pre Init-')
        # print('Class name:   ', cls.__name__,)
        # print('Init params:  ', initializer.__code__.co_varnames)
        # print('Param values: ', kwargs)
        if not others and not kwargs:
            # Dataclasses cannot be constructed without passing any args or kwargs because __init__ will throw. However,
            # pickle doesn't use the dataclass __init__() function to unpickle an object. Pickle rather calls this
            # function (__new__) with no args or kwargs, expecting to get a blank instance of the object. It then gets
            # a pointer to the ret.__dict__, which is the storage container for all of the class state. Unpickle then
            # iterates over the keys in the state dict that it saved out, and puts them into rect.__dict__. Thus unpickle
            # does not use our initializer at all. We need to support this kind of initialization, which by the way
            # is probably how Python does it too. Python calls __new__ and then calls __init__ automatically. We're
            # interrupting that process by calling the __init__ within the __new__, so we need to support cases when
            # callers are expecting that they can create an empty object using __new__ by itself. For reference, go to
            #   anaconda3/envs/pytorch_latest_p37/lib/python3.7/pickle.py
            #       class _Unpickler:
            #           def load_build(self):
            #               state = self.stack.pop()
            #               if state:
            #                   # State has your saved dataclass fields in it
            #                   inst_dict = inst.__dict__
            #                   for k, v in state.items():
            #                      inst_dict[k] = v
            #
            # Note, I have simplified the code slightly for exposition here. Also, this python code probably is not
            # running in practice, because pickle has a compiled version that runs instead. Near the bottom of the file
            # you'll find "from _pickle import" [...] except ImportError. Throw an import error intentionally there, and
            # the python pickle code will run so you can debug.
            return ret

        try:
            initializer(ret, *others, **kwargs)
        except Exception as e:
            should_stop = "missing" in str(e) and "required positional argument" in str(e)
            should_stop |= "got an unexpected keyword argument" in str(e)
            if should_stop:
                print("")
                print("CONFIG IS NOT CONSTRUCTING.")
                print("CONFIG IS NOT CONSTRUCTING.")
                print("CONFIG IS NOT CONSTRUCTING.")
                print("")
                print("The error message is:")
                print("")
                print(f"    {e}")
                print("")
                print("CONFIG IS NOT CONSTRUCTING.")
                print("CONFIG IS NOT CONSTRUCTING.")
                print("CONFIG IS NOT CONSTRUCTING.")
                print("")

            raise

        return ret

    @property
    def inputs(self) -> Config:
        return self


@dataclass
class Nullable:
    """Derive from this to make dataclasses that can be set to null by setting all of the fields to None.
    Setting all fields to None is helpful because it preserves the type when serializing dataclasses.
    """

    @property
    def is_null(self):
        for key in self.__dataclass_fields__.keys():
            if self.__dict__[key] is not None:
                return False

        return True

    def set_null(self):
        for key in self.__dataclass_fields__.keys():
            self.__dict__[key] = None

    @classmethod
    def make_null(cls):
        fields = cls.__dict__["__dataclass_fields__"]
        return cls(*[None for _ in range(len(fields))])
