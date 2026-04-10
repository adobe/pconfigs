# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

from dataclasses import dataclass
from os import path

from pconfigs.pinnable import pconfig, pconfiged, pproperty


# 1) No properties shadowing fields -> should NOT stub (with default stub=True permitting stubbing)
@pconfig
class NoProp:
    a: int
    b: int


def test_no_stub_when_no_properties():
    # No base in MRO should have a name starting with "Stubbed"
    assert not any(base.__name__.startswith("Stubbed") for base in NoProp.mro())
    x = NoProp(a=1, b=2)
    assert x.a == 1 and x.b == 2


# 2) Property shadowing a field name -> should stub automatically (because stub=True permits it)
@pconfig
class WithProp:
    a: int
    b: int

    @pproperty
    def a(self) -> int:
        return self.b * 2


def test_stub_when_property_present():
    # There should be a stub base in the MRO
    assert any(base.__name__.startswith("Stubbed") for base in WithProp.mro())
    x = WithProp(a=1, b=3)
    # a is a computed property; inputs are provided via PropInputs
    assert x.a == 6 and x.b == 3


# 3) If user explicitly disables stubbing while having a property, dataclass should error
def test_disabling_stub_raises_for_property_shadowing():
    error_raised = False
    try:

        @pconfig(legacy_mode=True)
        class Bad:
            a: int
            b: int

            @pproperty
            def a(self) -> int:
                return self.b * 2

    except TypeError as e:
        error_raised = True

    assert error_raised, "Expected TypeError when stub=False and a property shadows a field"


# 3) If user explicitly disables stubbing and its not needed either, things should work fine.
def test_disabling_stub_works_when_no_stubbing_needed():
    error_raised = False
    try:

        @pconfig(legacy_mode=True)
        class Good:
            a: int
            b: int

    except Exception as e:
        error_raised = True

    assert not error_raised, "Expected no error when stub=False and no stubbing is needed"


test_no_stub_when_no_properties()
test_stub_when_property_present()
test_disabling_stub_raises_for_property_shadowing()
print(f"{path.basename(__file__)}  Conditional stubbing tests passed.")
