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

from pconfigs import Pin, Pinned, pconfig, pdefaults, pinputs, pproperty
from tests.t035_helpers import truetype


@pconfig(calls=truetype)
class TruetypeFunc:
    font: Pinned[str]
    basename: str

    @pproperty
    def font(self) -> str:
        return os.path.join("some/path", self.basename)


pdefaults += TruetypeFunc(
    font=Pinned,
    basename="NotoSans-Regular.ttf",
    size=18,
)

try:
    pdefaults += TruetypeFunc(
        font=Pinned,
        basename="NotoSans-Regular.ttf_different",
        size=18,
    )
    raise ValueError("Expected a ValueError that prevents us from changing the default config.")
except ValueError as e:
    msg = "The default config for TruetypeFunc is already set. You can't make 2 defaults."
    if msg not in str(e):
        raise ValueError(f"Expected a ValueError with message '{msg}'.")


font_config = pdefaults(TruetypeFunc)
font = font_config()


#### Check that the user is able to override the default annotation for function parameters that don't have a default.
#### This was a bug in an earlier version of pconfig because we only created annotations for params that had a default.
#### But we want to allow the user to be able to change the annotation (e.g., to Pinned, or even to restrict the type).
def my_func_with_default_arg(x: float, y: float, slope: float = 1.0) -> float:
    return x * slope + y


@pconfig(calls=my_func_with_default_arg)
class MyFuncWithDefaultArg:
    y: Pinned[float]
    slope: Pinned[float]


pdefaults += MyFuncWithDefaultArg(
    y=Pin(2.0),
    slope=Pin(2.0),
)

line_with_y = next(line for line in str(pdefaults(MyFuncWithDefaultArg)).split("\n") if re.search(r"\by\s*=", line))
if "Pinned" not in line_with_y:
    raise ValueError("Expected the printed value of parameter 'y' to note that it is a Pinned value.")

print(f"{os.path.basename(__file__)}  @pconfig kwarg-mock function with added fields and pinning works.")
