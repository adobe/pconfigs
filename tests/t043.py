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

from pconfigs.pinnable import Pin, Pinned, pconfig, pdefaults, pinputs, pproperty


class MyClass:
    @staticmethod
    def my_staticmethod(value: str) -> bool:
        print(f"value: {value}")
        return True

    @classmethod
    def my_classmethod(cls, value: str) -> bool:
        print(f"value: {value}")
        return True


@pconfig(calls=MyClass.my_staticmethod)
class MyStaticMethod:
    pass


my_static_method = MyStaticMethod()
result = my_static_method(value="test")
assert result == True


@pconfig(calls=MyClass.my_classmethod)
class MyClassMethod:
    pass


my_class_method = MyClassMethod()
result = my_class_method(value="test")
assert result == True

print(f"{os.path.basename(__file__)}  @pconfig tests can call classmethods and staticmethods.")
