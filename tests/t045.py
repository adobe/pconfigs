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
from pathlib import Path, PurePath
from typing import Callable, Dict, List, Mapping, MutableMapping, MutableSequence, Optional, Sequence, Tuple, Union

from pconfigs import Omitted, pconfig, pdefaults


#### Test 1: Simply-typed __init__ params are auto-added; complex-typed params are not.
class MixedTypesClass:
    def __init__(
        self,
        model: Optional[Callable] = None,
        *,
        fullgraph: bool = False,
        dynamic: Optional[bool] = None,
        backend: Union[str, Callable] = "inductor",
        mode: Optional[str] = None,
        options: Optional[Dict[str, Union[str, int, bool, Callable]]] = None,
        disable: bool = False,
    ):
        self.model = model
        self.fullgraph = fullgraph
        self.dynamic = dynamic
        self.backend = backend
        self.mode = mode
        self.options = options
        self.disable = disable


@pconfig(mocks=MixedTypesClass)
class MixedTypesClassConfig:
    model: Omitted[Callable]
    options: Omitted[dict]


mixed_types_class_config = MixedTypesClassConfig(backend="eager", mode="fast")
config_fields = set(mixed_types_class_config.asdict().keys())

assert "fullgraph" in config_fields, "fullgraph (bool) should be auto-added."
assert "dynamic" in config_fields, "dynamic (Optional[bool]) should be auto-added."
assert "backend" in config_fields, "backend (Union[str, Callable]) should be auto-added."
assert "mode" in config_fields, "mode (Optional[str]) should be auto-added."
assert "disable" in config_fields, "disable (bool) should be auto-added."

obj = mixed_types_class_config.construct()
assert obj.backend == "eager", f"Test 1 failed: backend={obj.backend}"
assert obj.mode == "fast", f"Test 1 failed: mode={obj.mode}"
assert obj.fullgraph is False, f"Test 1 failed: fullgraph={obj.fullgraph}"
assert obj.model is None, "Test 1 failed: Omitted model should use external default (None)."


#### Test 2: Positional-only __init__ params are never auto-added.
class PositionalOnlyClass:
    def __init__(self, x: int = 0, /, y: int = 1, z: int = 2):
        self.x = x
        self.y = y
        self.z = z


@pconfig(mocks=PositionalOnlyClass)
class PositionalOnlyClassConfig:
    pass


positional_only_class_config = PositionalOnlyClassConfig(y=10, z=20)
config_fields = set(positional_only_class_config.asdict().keys())

assert "x" not in config_fields, "x (positional-only) should not be auto-added."
assert "y" in config_fields, "y (positional-or-keyword, simple) should be auto-added."
assert "z" in config_fields, "z (positional-or-keyword, simple) should be auto-added."

obj = positional_only_class_config.construct()
assert obj.y == 10, f"Test 2 failed: y={obj.y}"
assert obj.z == 20, f"Test 2 failed: z={obj.z}"


#### Test 3: All-positional-or-keyword simple __init__ params ARE auto-added.
class SimpleKwargClass:
    def __init__(self, x: float, param_a: float = 1.0, param_b: str = "hello"):
        self.x = x
        self.param_a = param_a
        self.param_b = param_b


@pconfig(mocks=SimpleKwargClass)
class SimpleKwargClassConfig:
    pass


simple_kwarg_class_config = SimpleKwargClassConfig(param_a=3.0, param_b="world")
config_fields = set(simple_kwarg_class_config.asdict().keys())

assert "x" not in config_fields, "x (no default) should not be auto-added."
assert "param_a" in config_fields, "param_a (float with default) should be auto-added."
assert "param_b" in config_fields, "param_b (str with default) should be auto-added."

obj = simple_kwarg_class_config.construct(x=2.0)
assert obj.param_a == 3.0, f"Test 3 failed: param_a={obj.param_a}"
assert obj.param_b == "world", f"Test 3 failed: param_b={obj.param_b}"
assert obj.x == 2.0, f"Test 3 failed: x={obj.x}"


#### Test 4: User-annotated __init__ params are always included regardless of type.
class ExplicitComplexClass:
    def __init__(
        self,
        callback: Optional[Callable] = None,
        *,
        rate: float = 1.0,
    ):
        self.callback = callback
        self.rate = rate


@pconfig(mocks=ExplicitComplexClass)
class ExplicitComplexClassConfig:
    callback: Optional[Callable]


explicit_complex_class_config = ExplicitComplexClassConfig(callback=lambda x: x * 2, rate=5.0)
config_fields = set(explicit_complex_class_config.asdict().keys())

assert "callback" in config_fields, "callback should be included when user explicitly annotates it."
assert "rate" in config_fields, "rate (float) should be auto-added."

obj = explicit_complex_class_config.construct()
assert obj.callback(3) == 6, f"Test 4 failed: callback(3)={obj.callback(3)}"
assert obj.rate == 5.0, f"Test 4 failed: rate={obj.rate}"


#### Test 5: Simple containers of simple types in __init__ are auto-added.
class ContainerClass:
    def __init__(
        self,
        tags: List[str] = None,
        counts: Tuple[int, int] = (0, 0),
        mapping: Dict[str, float] = None,
        complex_mapping: Dict[str, Callable] = None,
    ):
        self.tags = tags
        self.counts = counts
        self.mapping = mapping
        self.complex_mapping = complex_mapping


@pconfig(mocks=ContainerClass)
class ContainerClassConfig:
    complex_mapping: Omitted[dict]


container_class_config = ContainerClassConfig(tags=["a", "b"], counts=(3, 4))
config_fields = set(container_class_config.asdict().keys())

assert "tags" in config_fields, "tags (List[str]) should be auto-added."
assert "counts" in config_fields, "counts (Tuple[int, int]) should be auto-added."
assert "mapping" in config_fields, "mapping (Dict[str, float]) should be auto-added."

obj = container_class_config.construct()
assert obj.tags == ["a", "b"], f"Test 5 failed: tags={obj.tags}"
assert obj.counts == (3, 4), f"Test 5 failed: counts={obj.counts}"
assert obj.complex_mapping is None, "Test 5 failed: Omitted complex_mapping should use external default."


#### Test 6: Union with any simple component at top level is auto-added for __init__.
class UnionTypesClass:
    def __init__(
        self,
        backend: Union[str, Callable] = "inductor",
        schedule: Union[Callable, None] = None,
    ):
        self.backend = backend
        self.schedule = schedule


@pconfig(mocks=UnionTypesClass)
class UnionTypesClassConfig:
    schedule: Omitted[Callable]


union_types_class_config = UnionTypesClassConfig(backend="eager")
config_fields = set(union_types_class_config.asdict().keys())

assert "backend" in config_fields, "backend (Union[str, Callable]) should be auto-added."

obj = union_types_class_config.construct()
assert obj.backend == "eager", f"Test 6 failed: backend={obj.backend}"
assert obj.schedule is None, "Test 6 failed: Omitted schedule should use external default."


#### Test 7: Default values with complex container contents are rejected for __init__.
class ComplexDefaultsClass:
    def __init__(
        self,
        simple_tuple: tuple = (1, 2, 3),
        complex_tuple: tuple = (lambda x: x,),
        simple_dict: dict = {"a": 1},
        complex_dict: dict = {"fn": lambda x: x},
        nested_simple: tuple = ((1, 2), (3, 4)),
        nested_complex: list = [(1, lambda x: x)],
        nested_dict: dict = {"a": {"b": 1, "c": (2, 3)}},
        nested_dict_complex: dict = {"a": {"b": lambda x: x}},
    ):
        self.simple_tuple = simple_tuple
        self.simple_dict = simple_dict
        self.nested_simple = nested_simple
        self.nested_dict = nested_dict


@pconfig(mocks=ComplexDefaultsClass)
class ComplexDefaultsClassConfig:
    complex_tuple: Omitted[tuple]
    complex_dict: Omitted[dict]
    nested_complex: Omitted[list]
    nested_dict_complex: Omitted[dict]


complex_defaults_class_config = ComplexDefaultsClassConfig(
    simple_tuple=(10, 20, 30),
    simple_dict={"a": 100},
    nested_simple=((5, 6), (7, 8)),
    nested_dict={"a": {"b": 50, "c": (2, 3)}},
)
config_fields = set(complex_defaults_class_config.asdict().keys())

assert "simple_tuple" in config_fields, "simple_tuple should be auto-added."
assert "simple_dict" in config_fields, "simple_dict should be auto-added."
assert "nested_simple" in config_fields, "nested_simple should be auto-added."
assert "nested_dict" in config_fields, "nested_dict should be auto-added."

obj = complex_defaults_class_config.construct()
assert obj.simple_tuple == (10, 20, 30), f"Test 7 failed: simple_tuple={obj.simple_tuple}"
assert obj.simple_dict == {"a": 100}, f"Test 7 failed: simple_dict={obj.simple_dict}"
assert obj.nested_simple == ((5, 6), (7, 8)), f"Test 7 failed: nested_simple={obj.nested_simple}"
assert obj.nested_dict == {"a": {"b": 50, "c": (2, 3)}}, f"Test 7 failed: nested_dict={obj.nested_dict}"


#### Test 8: Path-typed __init__ parameters are auto-added.
class PathTypesClass:
    def __init__(
        self,
        output_path: Path = None,
        base_path: PurePath = None,
        callback: Callable = None,
    ):
        self.output_path = output_path
        self.base_path = base_path
        self.callback = callback


@pconfig(mocks=PathTypesClass)
class PathTypesClassConfig:
    callback: Omitted[Callable]


path_types_class_config = PathTypesClassConfig(output_path=Path("/out"), base_path=PurePath("/base"))
config_fields = set(path_types_class_config.asdict().keys())

assert "output_path" in config_fields, "output_path (Path) should be auto-added."
assert "base_path" in config_fields, "base_path (PurePath) should be auto-added."

obj = path_types_class_config.construct()
assert obj.output_path == Path("/out"), f"Test 8 failed: output_path={obj.output_path}"
assert obj.base_path == PurePath("/base"), f"Test 8 failed: base_path={obj.base_path}"
assert obj.callback is None, "Test 8 failed: Omitted callback should use external default."


#### Test 9: bytes-typed __init__ parameters are auto-added.
class BytesTypeClass:
    def __init__(
        self,
        data: bytes = b"",
        name: str = "default",
    ):
        self.data = data
        self.name = name


@pconfig(mocks=BytesTypeClass)
class BytesTypeClassConfig:
    pass


bytes_type_class_config = BytesTypeClassConfig(data=b"hello", name="test")
config_fields = set(bytes_type_class_config.asdict().keys())

assert "data" in config_fields, "data (bytes) should be auto-added."
assert "name" in config_fields, "name (str) should be auto-added."

obj = bytes_type_class_config.construct()
assert obj.data == b"hello", f"Test 9 failed: data={obj.data}"
assert obj.name == "test", f"Test 9 failed: name={obj.name}"


#### Test 10: Abstract container annotations in __init__ are auto-added.
class AbstractContainersClass:
    def __init__(
        self,
        items: Sequence[int] = (1, 2, 3),
        mutable_items: MutableSequence[str] = None,
        lookup: Mapping[str, float] = None,
        mutable_lookup: MutableMapping[str, int] = None,
        complex_seq: Sequence[Callable] = None,
    ):
        self.items = items
        self.mutable_items = mutable_items
        self.lookup = lookup
        self.mutable_lookup = mutable_lookup
        self.complex_seq = complex_seq


@pconfig(mocks=AbstractContainersClass)
class AbstractContainersClassConfig:
    complex_seq: Omitted[Sequence]


abstract_containers_class_config = AbstractContainersClassConfig(items=(10, 20, 30), lookup={"x": 1.5})
config_fields = set(abstract_containers_class_config.asdict().keys())

assert "items" in config_fields, "items (Sequence[int]) should be auto-added."
assert "mutable_items" in config_fields, "mutable_items (MutableSequence[str]) should be auto-added."
assert "lookup" in config_fields, "lookup (Mapping[str, float]) should be auto-added."
assert "mutable_lookup" in config_fields, "mutable_lookup (MutableMapping[str, int]) should be auto-added."

obj = abstract_containers_class_config.construct()
assert obj.items == (10, 20, 30), f"Test 10 failed: items={obj.items}"
assert obj.lookup == {"x": 1.5}, f"Test 10 failed: lookup={obj.lookup}"
assert obj.complex_seq is None, "Test 10 failed: Omitted complex_seq should use external default."


#### Test 11: Optional[Path] and Union[str, Path] in __init__ are auto-added.
class OptionalPathClass:
    def __init__(
        self,
        config_path: Optional[Path] = None,
        output: Union[str, Path] = "stdout",
    ):
        self.config_path = config_path
        self.output = output


@pconfig(mocks=OptionalPathClass)
class OptionalPathClassConfig:
    pass


optional_path_class_config = OptionalPathClassConfig(config_path=Path("/etc/config"), output="stderr")
config_fields = set(optional_path_class_config.asdict().keys())

assert "config_path" in config_fields, "config_path (Optional[Path]) should be auto-added."
assert "output" in config_fields, "output (Union[str, Path]) should be auto-added."

obj = optional_path_class_config.construct()
assert obj.config_path == Path("/etc/config"), f"Test 11 failed: config_path={obj.config_path}"
assert obj.output == "stderr", f"Test 11 failed: output={obj.output}"


#### Test 12: Path default values in __init__ are recognized as simply typed.
class PathDefaultsClass:
    def __init__(
        self,
        root: Path = Path("/tmp"),
        name: str = "default",
    ):
        self.root = root
        self.name = name


@pconfig(mocks=PathDefaultsClass)
class PathDefaultsClassConfig:
    pass


path_defaults_class_config = PathDefaultsClassConfig(root=Path("/data"), name="output")
config_fields = set(path_defaults_class_config.asdict().keys())

assert "root" in config_fields, "root (Path with Path default) should be auto-added."
assert "name" in config_fields, "name (str) should be auto-added."

obj = path_defaults_class_config.construct()
assert obj.root == Path("/data"), f"Test 12 failed: root={obj.root}"
assert obj.name == "output", f"Test 12 failed: name={obj.name}"


#### Test 13: TypeError is raised for complex params not handled by user.
class UnhandledComplexClass:
    def __init__(
        self,
        name: str = "default",
        callback: Callable = None,
    ):
        self.name = name
        self.callback = callback


try:

    @pconfig(mocks=UnhandledComplexClass)
    class UnhandledComplexClassConfig:
        pass

    assert False, "Test 13 failed: TypeError should have been raised for unhandled complex param."
except TypeError as e:
    assert "callback" in str(e), f"Test 13 failed: error should mention 'callback', got: {e}"


@pconfig(mocks=UnhandledComplexClass)
class UnhandledComplexClassConfigWithOmit:
    callback: Omitted[Callable]


omit_config = UnhandledComplexClassConfigWithOmit(name="test")
obj = omit_config.construct()
assert obj.name == "test", f"Test 13 failed: name={obj.name}"
assert obj.callback is None, "Test 13 failed: Omitted callback should use external default."


@pconfig(mocks=UnhandledComplexClass)
class UnhandledComplexClassConfigWithSimpleType:
    callback: Callable


simple_type_config = UnhandledComplexClassConfigWithSimpleType(name="test2", callback=lambda x: x + 1)
obj = simple_type_config.construct()
assert obj.name == "test2", f"Test 13 failed: name={obj.name}"
assert obj.callback(5) == 6, f"Test 13 failed: callback(5)={obj.callback(5)}"


#### Test 14: Enum-typed params are auto-added; enum defaults are recognized.
from enum import Enum


class Color(Enum):
    Red = "red"
    Blue = "blue"


class EnumClass:
    def __init__(
        self,
        color: Color = Color.Red,
        name: str = "default",
    ):
        self.color = color
        self.name = name


@pconfig(mocks=EnumClass)
class EnumClassConfig:
    pass


enum_class_config = EnumClassConfig(color=Color.Blue, name="test")
config_fields = set(enum_class_config.asdict().keys())

assert "color" in config_fields, "color (Enum) should be auto-added."
assert "name" in config_fields, "name (str) should be auto-added."

obj = enum_class_config.construct()
assert obj.color is Color.Blue, f"Test 14 failed: color={obj.color}"
assert obj.name == "test", f"Test 14 failed: name={obj.name}"

enum_default_config = EnumClassConfig()
obj = enum_default_config.construct()
assert obj.color is Color.Red, f"Test 14 failed: default color={obj.color}"


#### Test 15: Optional[Enum] params are auto-added.
class OptionalEnumClass:
    def __init__(
        self,
        color: Optional[Color] = None,
        name: str = "default",
    ):
        self.color = color
        self.name = name


@pconfig(mocks=OptionalEnumClass)
class OptionalEnumClassConfig:
    pass


optional_enum_config = OptionalEnumClassConfig(color=Color.Blue)
config_fields = set(optional_enum_config.asdict().keys())

assert "color" in config_fields, "color (Optional[Enum]) should be auto-added."

obj = optional_enum_config.construct()
assert obj.color is Color.Blue, f"Test 15 failed: color={obj.color}"

optional_enum_default = OptionalEnumClassConfig()
obj = optional_enum_default.construct()
assert obj.color is None, f"Test 15 failed: default color={obj.color}"


#### Test 16: TypeError is raised for non-None complex-defaulted params not handled by user.
class LambdaDefaultClass:
    def __init__(
        self,
        name: str = "default",
        transform: Callable = lambda x: x * 2,
    ):
        self.name = name
        self.transform = transform


try:

    @pconfig(mocks=LambdaDefaultClass)
    class UnhandledLambdaDefaultClassConfig:
        pass

    assert False, "Test 16 failed: TypeError should have been raised for unhandled complex param."
except TypeError as e:
    assert "transform" in str(e), f"Test 16 failed: error should mention 'transform', got: {e}"


@pconfig(mocks=LambdaDefaultClass)
class HandledLambdaDefaultClassConfigWithOmit:
    transform: Omitted[Callable]


omit_config = HandledLambdaDefaultClassConfigWithOmit(name="test")
obj = omit_config.construct()
assert obj.name == "test", f"Test 16 failed: name={obj.name}"
assert obj.transform(3) == 6, f"Test 16 failed: Omitted transform should use external default lambda."


#### Test 17: Params without type hints have types inferred from defaults.
class NoHintsClass:
    def __init__(
        self,
        count=10,
        name="hello",
        flag=True,
        rate=0.5,
    ):
        self.count = count
        self.name = name
        self.flag = flag
        self.rate = rate


@pconfig(mocks=NoHintsClass)
class NoHintsClassConfig:
    pass


no_hints_config = NoHintsClassConfig(count=42, name="world", flag=False, rate=1.5)
config_fields = set(no_hints_config.asdict().keys())

assert "count" in config_fields, "Test 17 failed: count (inferred int) should be auto-added."
assert "name" in config_fields, "Test 17 failed: name (inferred str) should be auto-added."
assert "flag" in config_fields, "Test 17 failed: flag (inferred bool) should be auto-added."
assert "rate" in config_fields, "Test 17 failed: rate (inferred float) should be auto-added."

obj = no_hints_config.construct()
assert obj.count == 42, f"Test 17 failed: count={obj.count}"
assert obj.name == "world", f"Test 17 failed: name={obj.name}"
assert obj.flag is False, f"Test 17 failed: flag={obj.flag}"
assert obj.rate == 1.5, f"Test 17 failed: rate={obj.rate}"

no_hints_default = NoHintsClassConfig()
obj = no_hints_default.construct()
assert obj.count == 10, f"Test 17 default failed: count={obj.count}"
assert obj.name == "hello", f"Test 17 default failed: name={obj.name}"
assert obj.flag is True, f"Test 17 default failed: flag={obj.flag}"
assert obj.rate == 0.5, f"Test 17 default failed: rate={obj.rate}"


#### Test 18: None default without type hint raises TypeError (unknown type).
class NoneNoHintClass:
    def __init__(
        self,
        name="default",
        callback=None,
    ):
        self.name = name
        self.callback = callback


try:

    @pconfig(mocks=NoneNoHintClass)
    class UnhandledNoneNoHintClassConfig:
        pass

    assert False, "Test 18 failed: TypeError should have been raised for None default without type hint."
except TypeError as e:
    assert "callback" in str(e), f"Test 18 failed: error should mention 'callback', got: {e}"
    assert "intended type is unknown" in str(e), f"Test 18 failed: error should say type is unknown, got: {e}"


@pconfig(mocks=NoneNoHintClass)
class HandledNoneNoHintClassConfigWithOmit:
    callback: Omitted[object]


omit_config = HandledNoneNoHintClassConfigWithOmit(name="test")
obj = omit_config.construct()
assert obj.name == "test", f"Test 18 failed: name={obj.name}"
assert obj.callback is None, "Test 18 failed: Omitted callback should use external default (None)."


#### Test 19: Complex default without type hint raises TypeError (inferred non-simple type).
class LambdaNoHintClass:
    def __init__(
        self,
        name="default",
        transform=lambda x: x + 1,
    ):
        self.name = name
        self.transform = transform


try:

    @pconfig(mocks=LambdaNoHintClass)
    class UnhandledLambdaNoHintClassConfig:
        pass

    assert False, "Test 19 failed: TypeError should have been raised for lambda default without type hint."
except TypeError as e:
    assert "transform" in str(e), f"Test 19 failed: error should mention 'transform', got: {e}"


@pconfig(mocks=LambdaNoHintClass)
class HandledLambdaNoHintClassConfigWithOmit:
    transform: Omitted[Callable]


omit_config = HandledLambdaNoHintClassConfigWithOmit(name="test")
obj = omit_config.construct()
assert obj.name == "test", f"Test 19 failed: name={obj.name}"
assert obj.transform(5) == 6, f"Test 19 failed: Omitted transform should use external default lambda."


print(f"{os.path.basename(__file__)}  Simply-typed config parameter rules (mocks): all tests passed.")
