# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from pconfigs import pconfig, pconfiged, pdefaults
from pconfigs.pinnable import pconfig, pdefaults


def line_func(x: float, slope: float = 1.0, offset: float = 0.0) -> float:
    return x * slope + offset


@pconfig(calls=line_func)
class LineFunc:
    pass


pdefaults += LineFunc(
    slope=4.0,
)
print(pdefaults(LineFunc))
# LineFunc(
#     funcname=__main__.line_func,  # ClassVar (omit from config)
#     slope=1.0,
#     offset=0.0,
# )


# @pconfiged(runnable=True)
# class LinePlotter:
#     config: LinePlotterConfig

#     def main(self, *args, **kwargs):
#         x = range(self.config.x_lo, self.config.x_hi)
#         y = [self.config.line_func(x=c) for c in x]
#         self.plot(x, y)


# @pconfig(constructs=LinePlotter)
# class LinePlotterConfig:
#     line_func: LineFunc
#     x_lo: int
#     x_hi: int


# pdefaults += LinePlotterConfig(
#     line_func=pdefaults(LineFunc),
#     x_lo=-10,
#     x_hi=10,
# )

# config = LinePlotter(
#     line_func=LineFunc(
#         slope=4.0,
#     )
# )
