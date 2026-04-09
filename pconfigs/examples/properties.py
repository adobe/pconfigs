# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

# 2. Properties

print("## 2.1 Define computed properties with `@pproperty`.")

from pconfigs import pconfig, pproperty


@pconfig
class LineConfig:
    m: float
    b: float

    @pproperty                     # @pproperty's are evaluated at construction time.
    def m(self) -> float:
        return 2 * self.b


line_config = LineConfig(
    m=1.0,
    b=1.0,                         # User input value will be replaced (see also §Pinning).
)

print(line_config)


print("## 2.2 Fix-up user input values with @pinputs.")

from pconfigs import pconfig, pdefaults, pinputs, pproperty


@pconfig
class VehicleConfig:
    make: str
    speed: float

    @pproperty
    def speed(self) -> float:
        user_input_speed = pinputs(self).speed   # Get property input value.
        return max(0, user_input_speed)


pdefaults += VehicleConfig(
    make="BMW",
    speed=80,
)

vehicle_config = VehicleConfig(
    speed=-1,                           # User sets out-of-bounds value.
)
print(vehicle_config)


print("## 2.3 Prevent users from setting computed properties.")

from typing import Tuple

from numpy.linalg import norm

from pconfigs import Pinned, pconfig, pproperty


@pconfig
class FancyVehicleConfig(VehicleConfig):
    speed: Pinned[float]
    velocity: Tuple[float, float]

    @pproperty
    def speed(self) -> float:
        return norm(self.velocity)


try:
    fancy_vehicle_config = FancyVehicleConfig(
        speed=-1,                                       # User cannot set a Pinned field.
        velocity=(50, 50),
    )
except Exception as e:
    print(str(e), "\n")

fancy_vehicle_config = FancyVehicleConfig(
    speed=Pinned,
    velocity=(50, 50),
)
print(fancy_vehicle_config)
