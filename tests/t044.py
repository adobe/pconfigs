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


#### Test 1: Simply-typed params are auto-added; complex-typed params are not.
def func_with_mixed_types(
    model: Optional[Callable] = None,
    *,
    fullgraph: bool = False,
    dynamic: Optional[bool] = None,
    backend: Union[str, Callable] = "inductor",
    mode: Optional[str] = None,
    options: Optional[Dict[str, Union[str, int, bool, Callable]]] = None,
    disable: bool = False,
) -> str:
    return f"{backend}:{mode}:{fullgraph}:{dynamic}:{disable}"


@pconfig(calls=func_with_mixed_types)
class MixedTypesFunc:
    model: Omitted[Callable]
    options: Omitted[dict]


mixed_types_func = MixedTypesFunc(backend="eager", mode="fast")
config_fields = set(mixed_types_func.asdict().keys())

assert "fullgraph" in config_fields, "fullgraph (bool) should be auto-added."
assert "dynamic" in config_fields, "dynamic (Optional[bool]) should be auto-added."
assert "backend" in config_fields, "backend (Union[str, Callable]) should be auto-added (str is simple)."
assert "mode" in config_fields, "mode (Optional[str]) should be auto-added."
assert "disable" in config_fields, "disable (bool) should be auto-added."

result = mixed_types_func()
assert result == "eager:fast:False:None:False", f"Test 1 call failed: {result}"


#### Test 2: Positional-only params are never auto-added.
def func_with_positional_only(x: int = 0, /, y: int = 1, z: int = 2) -> int:
    return x + y + z


@pconfig(calls=func_with_positional_only)
class PositionalOnlyFunc:
    pass


positional_only_func = PositionalOnlyFunc(y=10, z=20)
config_fields = set(positional_only_func.asdict().keys())

assert "x" not in config_fields, "x (positional-only) should not be auto-added."
assert "y" in config_fields, "y (positional-or-keyword, simple) should be auto-added."
assert "z" in config_fields, "z (positional-or-keyword, simple) should be auto-added."

result = positional_only_func(5)
assert result == 35, f"Test 2 call failed: expected 35, got {result}"


#### Test 3: All-positional-or-keyword simple params ARE auto-added (no * separator).
def simple_kwarg_func(x: float, param_a: float = 1.0, param_b: str = "hello") -> str:
    return f"{x * param_a}:{param_b}"


@pconfig(calls=simple_kwarg_func)
class SimpleKwargFunc:
    pass


simple_kwarg_func_config = SimpleKwargFunc(param_a=3.0, param_b="world")
config_fields = set(simple_kwarg_func_config.asdict().keys())

assert "x" not in config_fields, "x (no default) should not be auto-added."
assert "param_a" in config_fields, "param_a (float with default) should be auto-added."
assert "param_b" in config_fields, "param_b (str with default) should be auto-added."

result = simple_kwarg_func_config(x=2.0)
assert result == "6.0:world", f"Test 3 call failed: {result}"


#### Test 4: User-annotated params are always included regardless of type.
def func_with_complex_arg(
    callback: Optional[Callable] = None,
    *,
    rate: float = 1.0,
) -> float:
    if callback is not None:
        return callback(rate)

    return rate


@pconfig(calls=func_with_complex_arg)
class ExplicitComplexFunc:
    callback: Optional[Callable]


explicit_complex_func = ExplicitComplexFunc(callback=lambda x: x * 2, rate=5.0)
config_fields = set(explicit_complex_func.asdict().keys())

assert "callback" in config_fields, "callback should be included when user explicitly annotates it."
assert "rate" in config_fields, "rate (float) should be auto-added."

result = explicit_complex_func()
assert result == 10.0, f"Test 4 call failed: expected 10.0, got {result}"


#### Test 5: Simple containers of simple types are auto-added.
def func_with_containers(
    tags: List[str] = None,
    counts: Tuple[int, int] = (0, 0),
    mapping: Dict[str, float] = None,
    complex_mapping: Dict[str, Callable] = None,
) -> str:
    return f"{tags}:{counts}"


@pconfig(calls=func_with_containers)
class ContainerFunc:
    complex_mapping: Omitted[dict]


container_func = ContainerFunc(tags=["a", "b"], counts=(3, 4))
config_fields = set(container_func.asdict().keys())

assert "tags" in config_fields, "tags (List[str]) should be auto-added."
assert "counts" in config_fields, "counts (Tuple[int, int]) should be auto-added."
assert "mapping" in config_fields, "mapping (Dict[str, float]) should be auto-added."

result = container_func()
assert result == "['a', 'b']:(3, 4)", f"Test 5 call failed: {result}"


#### Test 6: Union with any simple component at top level is auto-added.
def func_with_union_types(
    backend: Union[str, Callable] = "inductor",
    schedule: Union[Callable, None] = None,
) -> str:
    return f"{backend}"


@pconfig(calls=func_with_union_types)
class UnionTypesFunc:
    schedule: Omitted[Callable]


union_types_func = UnionTypesFunc(backend="eager")
config_fields = set(union_types_func.asdict().keys())

assert "backend" in config_fields, "backend (Union[str, Callable]) should be auto-added (str is simple)."

result = union_types_func()
assert result == "eager", f"Test 7 call failed: {result}"


#### Test 8: Calling a function config with simply-typed params works end to end.
def add_values(x: float, *, offset: float = 0.0, scale: float = 1.0) -> float:
    return x * scale + offset


@pconfig(calls=add_values)
class AddValuesFunc:
    pass


add_values_func = AddValuesFunc(offset=10.0, scale=2.0)
result = add_values_func(x=5.0)

assert result == 20.0, f"Test 8 call failed: expected 20.0, got {result}"


#### Test 9: Default values with complex container contents are rejected.
def func_with_complex_defaults(
    simple_tuple: tuple = (1, 2, 3),
    complex_tuple: tuple = (lambda x: x,),
    simple_dict: dict = {"a": 1},
    complex_dict: dict = {"fn": lambda x: x},
    nested_simple: tuple = ((1, 2), (3, 4)),
    nested_complex: list = [(1, lambda x: x)],
    nested_dict: dict = {"a": {"b": 1, "c": (2, 3)}},
    nested_dict_complex: dict = {"a": {"b": lambda x: x}},
) -> int:
    return sum(simple_tuple) + simple_dict["a"] + nested_simple[0][0] + nested_dict["a"]["b"]


@pconfig(calls=func_with_complex_defaults)
class ComplexDefaultsFunc:
    complex_tuple: Omitted[tuple]
    complex_dict: Omitted[dict]
    nested_complex: Omitted[list]
    nested_dict_complex: Omitted[dict]


complex_defaults_func = ComplexDefaultsFunc(
    simple_tuple=(10, 20, 30),
    simple_dict={"a": 100},
    nested_simple=((5, 6), (7, 8)),
    nested_dict={"a": {"b": 50, "c": (2, 3)}},
)
config_fields = set(complex_defaults_func.asdict().keys())

assert "simple_tuple" in config_fields, "simple_tuple ((1,2,3)) should be auto-added."
assert "simple_dict" in config_fields, "simple_dict ({'a': 1}) should be auto-added."
assert "nested_simple" in config_fields, "nested_simple (nested tuples of ints) should be auto-added."
assert "nested_dict" in config_fields, "nested_dict (dict of dict of simple types) should be auto-added."

result = complex_defaults_func()
assert result == 215, f"Test 9 call failed: expected 215, got {result}"


#### Test 10: Path-typed parameters are auto-added.
def func_with_path_types(
    output_path: Path = None,
    base_path: PurePath = None,
    callback: Callable = None,
) -> str:
    return f"{output_path}:{base_path}"


@pconfig(calls=func_with_path_types)
class PathTypesFunc:
    callback: Omitted[Callable]


path_types_func = PathTypesFunc(output_path=Path("/out"), base_path=PurePath("/base"))
config_fields = set(path_types_func.asdict().keys())

assert "output_path" in config_fields, "output_path (Path) should be auto-added."
assert "base_path" in config_fields, "base_path (PurePath) should be auto-added."

result = path_types_func()
assert result == "/out:/base", f"Test 10 call failed: {result}"


#### Test 11: bytes-typed parameters are auto-added.
def func_with_bytes_type(
    data: bytes = b"",
    name: str = "default",
) -> str:
    return f"{name}:{len(data)}"


@pconfig(calls=func_with_bytes_type)
class BytesTypeFunc:
    pass


bytes_type_func = BytesTypeFunc(data=b"hello", name="test")
config_fields = set(bytes_type_func.asdict().keys())

assert "data" in config_fields, "data (bytes) should be auto-added."
assert "name" in config_fields, "name (str) should be auto-added."

result = bytes_type_func()
assert result == "test:5", f"Test 11 call failed: {result}"


#### Test 12: Abstract container annotations (Sequence, Mapping, etc.) are auto-added.
def func_with_abstract_containers(
    items: Sequence[int] = (1, 2, 3),
    mutable_items: MutableSequence[str] = None,
    lookup: Mapping[str, float] = None,
    mutable_lookup: MutableMapping[str, int] = None,
    complex_seq: Sequence[Callable] = None,
) -> int:
    return sum(items)


@pconfig(calls=func_with_abstract_containers)
class AbstractContainersFunc:
    complex_seq: Omitted[Sequence]


abstract_containers_func = AbstractContainersFunc(items=(10, 20, 30))
config_fields = set(abstract_containers_func.asdict().keys())

assert "items" in config_fields, "items (Sequence[int]) should be auto-added."
assert "mutable_items" in config_fields, "mutable_items (MutableSequence[str]) should be auto-added."
assert "lookup" in config_fields, "lookup (Mapping[str, float]) should be auto-added."
assert "mutable_lookup" in config_fields, "mutable_lookup (MutableMapping[str, int]) should be auto-added."

result = abstract_containers_func()
assert result == 60, f"Test 12 call failed: expected 60, got {result}"


#### Test 13: Optional[Path] and Union[str, Path] are auto-added.
def func_with_optional_path(
    config_path: Optional[Path] = None,
    output: Union[str, Path] = "stdout",
) -> str:
    return f"{config_path}:{output}"


@pconfig(calls=func_with_optional_path)
class OptionalPathFunc:
    pass


optional_path_func = OptionalPathFunc(config_path=Path("/etc/config"), output="stderr")
config_fields = set(optional_path_func.asdict().keys())

assert "config_path" in config_fields, "config_path (Optional[Path]) should be auto-added."
assert "output" in config_fields, "output (Union[str, Path]) should be auto-added."

result = optional_path_func()
assert result == "/etc/config:stderr", f"Test 13 call failed: {result}"


#### Test 14: Path default values are recognized as simply typed.
def func_with_path_defaults(
    root: Path = Path("/tmp"),
    name: str = "default",
) -> str:
    return f"{root}/{name}"


@pconfig(calls=func_with_path_defaults)
class PathDefaultsFunc:
    pass


path_defaults_func = PathDefaultsFunc(root=Path("/data"), name="output")
config_fields = set(path_defaults_func.asdict().keys())

assert "root" in config_fields, "root (Path with Path default) should be auto-added."
assert "name" in config_fields, "name (str) should be auto-added."

result = path_defaults_func()
assert result == "/data/output", f"Test 14 call failed: {result}"


#### Test 15: Enum-typed params are auto-added; enum defaults are recognized.
from enum import Enum


class Color(Enum):
    Red = "red"
    Blue = "blue"


def func_with_enum(
    color: Color = Color.Red,
    name: str = "default",
) -> str:
    return f"{color.value}:{name}"


@pconfig(calls=func_with_enum)
class EnumFunc:
    pass


enum_func = EnumFunc(color=Color.Blue, name="test")
config_fields = set(enum_func.asdict().keys())

assert "color" in config_fields, "color (Enum) should be auto-added."
assert "name" in config_fields, "name (str) should be auto-added."

result = enum_func()
assert result == "blue:test", f"Test 15 call failed: {result}"

enum_default = EnumFunc()
result = enum_default()
assert result == "red:default", f"Test 15 default call failed: {result}"


#### Test 16: Optional[Enum] params are auto-added.
def func_with_optional_enum(
    color: Optional[Color] = None,
    name: str = "default",
) -> str:
    return f"{color}:{name}"


@pconfig(calls=func_with_optional_enum)
class OptionalEnumFunc:
    pass


optional_enum_func = OptionalEnumFunc(color=Color.Blue)
config_fields = set(optional_enum_func.asdict().keys())

assert "color" in config_fields, "color (Optional[Enum]) should be auto-added."

result = optional_enum_func()
assert result == "Color.Blue:default", f"Test 16 call failed: {result}"

optional_enum_default = OptionalEnumFunc()
result = optional_enum_default()
assert result == "None:default", f"Test 16 default call failed: {result}"


#### Test 17: TypeError is raised for complex-defaulted params not handled by user.
def func_with_lambda_default(
    name: str = "default",
    transform: Callable = lambda x: x * 2,
) -> str:
    return f"{name}:{transform(3)}"


try:

    @pconfig(calls=func_with_lambda_default)
    class UnhandledLambdaFunc:
        pass

    assert False, "Test 17 failed: TypeError should have been raised for unhandled complex param."
except TypeError as e:
    assert "transform" in str(e), f"Test 17 failed: error should mention 'transform', got: {e}"


@pconfig(calls=func_with_lambda_default)
class HandledLambdaFuncWithOmit:
    transform: Omitted[Callable]


omit_func = HandledLambdaFuncWithOmit(name="test")
result = omit_func()
assert result == "test:6", f"Test 17 Omitted call failed: {result}"


#### Test 18: Params without type hints have types inferred from defaults.
def func_no_hints(
    count=10,
    name="hello",
    flag=True,
    rate=0.5,
) -> str:
    return f"{count}:{name}:{flag}:{rate}"


@pconfig(calls=func_no_hints)
class NoHintsFunc:
    pass


no_hints_func = NoHintsFunc(count=42, name="world", flag=False, rate=1.5)
config_fields = set(no_hints_func.asdict().keys())

assert "count" in config_fields, "Test 18 failed: count (inferred int) should be auto-added."
assert "name" in config_fields, "Test 18 failed: name (inferred str) should be auto-added."
assert "flag" in config_fields, "Test 18 failed: flag (inferred bool) should be auto-added."
assert "rate" in config_fields, "Test 18 failed: rate (inferred float) should be auto-added."

result = no_hints_func()
assert result == "42:world:False:1.5", f"Test 18 call failed: {result}"

no_hints_default = NoHintsFunc()
result = no_hints_default()
assert result == "10:hello:True:0.5", f"Test 18 default call failed: {result}"


#### Test 19: None default without type hint raises TypeError (unknown type).
def func_none_no_hint(
    name="default",
    callback=None,
) -> str:
    return f"{name}:{callback}"


try:

    @pconfig(calls=func_none_no_hint)
    class UnhandledNoneNoHintFunc:
        pass

    assert False, "Test 19 failed: TypeError should have been raised for None default without type hint."
except TypeError as e:
    assert "callback" in str(e), f"Test 19 failed: error should mention 'callback', got: {e}"
    assert "intended type is unknown" in str(e), f"Test 19 failed: error should say type is unknown, got: {e}"


@pconfig(calls=func_none_no_hint)
class HandledNoneNoHintFuncWithOmit:
    callback: Omitted[object]


omit_func = HandledNoneNoHintFuncWithOmit(name="test")
result = omit_func()
assert result == "test:None", f"Test 19 Omitted call failed: {result}"


#### Test 20: Complex default without type hint raises TypeError (inferred non-simple type).
def func_lambda_no_hint(
    name="default",
    transform=lambda x: x + 1,
) -> str:
    return f"{name}:{transform(5)}"


try:

    @pconfig(calls=func_lambda_no_hint)
    class UnhandledLambdaNoHintFunc:
        pass

    assert False, "Test 20 failed: TypeError should have been raised for lambda default without type hint."
except TypeError as e:
    assert "transform" in str(e), f"Test 20 failed: error should mention 'transform', got: {e}"


@pconfig(calls=func_lambda_no_hint)
class HandledLambdaNoHintFuncWithOmit:
    transform: Omitted[Callable]


omit_func = HandledLambdaNoHintFuncWithOmit(name="test")
result = omit_func()
assert result == "test:6", f"Test 20 Omitted call failed: {result}"


print(f"{os.path.basename(__file__)}  Simply-typed config parameter rules: all tests passed.")
