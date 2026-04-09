# Properties

 (subsec-define-computed-properties-with-pproperty)=
## Define computed properties with `@pproperty`.

```python
from pconfigs import pconfig, pproperty

@pconfig
class LineConfig:
    m: float                       # PConfigs are dataclasses that hold config.
    b: float                       # All dataclass fields must be annotated.

    @pproperty                     # @pproperty's are dataclass fields whose
    def m(self) -> float:          # value is computed at construction time.
        return 2 * self.b


line_config = LineConfig(
    m=1.0,                         # Input value will be replaced (see also ¶3 below).
    b=1.0,
)

>>> print(line_config)
>>> LineConfig(
>>>     m=2.0,                     # Line config contains the computed value of m.
>>>     b=1.0,
>>> )
```


 (subsec-modify-user-input-values-with-pinputs)=
## Modify user input values with `@pinputs`.

```python
from pconfigs import pinputs, pdefaults

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
    speed=-1,
)

>>> print(vehicle_config)
>>> VehicleConfig(
>>>     make="BMW",
>>>     speed=0,                                 # Computed property corrects the value.
>>> )
```


 (subsec-prevent-users-from-setting-computed-properties)=
## Prevent users from setting computed properties.

```python
from pconfigs import Pinned

@pconfig
class FancyVehicleConfig(VehicleConfig):
    speed: Pinned[float]                            # Input is not accepted. Mark as Pinned.
    velocity: Tuple[float, float]

    @pproperty
    def speed(self) -> float:
        return norm(self.velocity)


fancy_vehicle_config = FancyVehicleConfig(
    speed=-1,                                       # User cannot set a Pinned field.
    velocity=(50, 50),
)
>>> ValueError: Cannot set a pinned field. Use FancyVehicleConfig.speed=Pinned 
>>> to fix this error.


fancy_vehicle_config = FancyVehicleConfig(
    speed=Pinned,
    velocity=(50, 50),
)
>>> print(fancy_vehicle_config)
>>> FancyVehicleConfig(
>>>     make="BMW",
>>>     speed=70.71067811865476,  # Pinned (omit from config)
>>>     velocity=(50, 50),
>>> )
```
