# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

import warnings
from os import path
from typing import Type

from pconfigs.pinnable import Pin, Pinned, pconfig, pconfiged, pproperty

# #### Test that a pconfiged class cannot be linked to the wrong config type
# @pconfiged
# class Test:
#     config: OtherThing


# try:

#     @pconfig(constructs=Test)
#     class TestConfig:
#         pass

#     raise Exception("A config was linked to the wrong constructable type, but an exception was not raised.")
# except Exception as e:
#     if "the @pconfiged type 'Test' expects a config of type" not in str(e):
#         raise e


class Test2:
    config: TestConfig


#### Test that a non-pconfiged class cannot be linked to a pconfig
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    try:

        @pconfig(constructs=Test2)
        class TestConfig:
            pass

        raise ValueError("Expected a ValueError to be raised.")

    except TypeError as e:
        if "'Test2' is not a @pconfiged class" not in str(e):
            raise e

    # desired_warning = "is being constructed as a pconfig class, and received received a single argument of type"
    # breakpoint()
    # if not any(desired_warning in str(w.message) for w in caught):
    #     breakpoint()
    #     raise AssertionError("Expected a warning to be emitted.")


#### Test that constructing a config class with a single positional argument that is a Type creates a warning.
#### This is not necessarily wrong, but its most likely a bug caused by the user forgetting to decorate the
#### constructable type as @pconfiged
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    try:

        @pconfig
        class TestConfig3:
            field: Type

        test_config3 = TestConfig3(Test2)

    except:
        pass

    desired_warning = "is being constructed as a pconfig class, and received received a single argument of type"
    if not any(desired_warning in str(w.message) for w in caught):
        raise AssertionError("Expected a warning to be emitted.")

#### Test that constructing a config class with a single kwarg argument that is a Type creates no warning.
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    try:

        @pconfig
        class TestConfig4:
            field: Type

        test_config4 = TestConfig4(field=Test2)

    except:
        pass

    desired_warning = "is being constructed as a pconfig class, and received received a single argument of type"
    if any(desired_warning in str(w.message) for w in caught):
        raise AssertionError("Expected no warnings to be emitted.")


#### Test that we can handle forward type references.
@pconfiged
class MyThing:
    config: MyThingConfig


@pconfig(constructs=MyThing)
class MyThingConfig:
    x: Something


Something = int

print(f"{path.basename(__file__)}  pconfig constructable class linking tests passed.")
