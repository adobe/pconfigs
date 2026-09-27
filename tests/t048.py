# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

import ast

from pconfigs import pconfig, pdefaults


@pconfig
class TupleItem:
    name: str


pdefaults += TupleItem(name="")


@pconfig
class TupleHolder:
    items: tuple


pdefaults += TupleHolder(items=())

for values in [
    (),
    (TupleItem(name="a"),),
    (TupleItem(name="a"), TupleItem(name="b")),
    (TupleItem(name="a"), 7),
]:
    rendered = TupleHolder(items=values).print_code()
    assert rendered.count("# NOTE:") == 1, rendered
    tree = ast.parse(rendered)
    holder = tree.body[-1].value
    items = next(keyword.value for keyword in holder.keywords if keyword.arg == "items")
    assert isinstance(items, ast.Tuple), rendered
    assert len(items.elts) == len(values), rendered
    for value, element in zip(values, items.elts):
        if isinstance(value, TupleItem):
            assert isinstance(element, ast.Call), rendered
            assert element.func.id == "TupleItem", rendered
            assert element.keywords[0].value.value == value.name, rendered
        else:
            assert element.value == value, rendered
