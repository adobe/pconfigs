# Construction

(subsec-configure-a-class)=
## Configure a class.

```python
from __future__ import annotations     # Forward references of typehints are required.

from pconfigs import pconfig, pconfiged, pdefaults

# Define a class that contains config.
@pconfiged
class Thing:
    config: ThingConfig                # A class' config is always called 'config'.

    def __init__(self):                # Constructor takes no arguments.
        pass

    def echo(self):
        print(self.config)             # config properties are automatically available.


# Define a config for the class (kept separate from the class).
@pconfig(constructs=Thing)
class ThingConfig:
    x: float
    y: float
    z: float


# Set default values for the config parameters (set separately to avoid clutter).
pdefaults += ThingConfig(
    x=1.0,
    y=2.0,
    z=3.0,
)
```


You can now do the following things.

 (subsec-construct-an-instance)=
## Construct an instance.

```python
thing_config = ThingConfig()
thing = thing_config.construct()   # Construct the pconfiged class.

>>> thing.echo()                   # Same output as above.
>>> ThingConfig(
>>>     constructable_type=Thing,  # ClassVar (omit from config)    # <- Printed comment
>>>     x=1.0,
>>>     y=2.0,
>>>     z=3.0,
>>> )
```

 (subsec-set-custom-config-values)=
## Set custom config values.
```python
another_thing_config = ThingConfig(
    y=2.2,
)

>>> print(another_thing_config)
>>> ThingConfig(
>>>     constructable_type=Thing,  # ClassVar (omit from config)    # <- Printed comment
>>>     x=1.0,
>>>     y=2.2,
>>>     z=3.0,
>>> )
```

 (subsec-copy-config-settings)=
## Copy config settings.
```python
last_thing_config = ThingConfig(
    another_thing_config,          # Values are auto-copied in for all non-set fields.
    x=1.1,
)

>>> print(last_thing_config)
>>> ThingConfig(
>>>     constructable_type=Thing,  # ClassVar (omit from config)    # <- Printed comment
>>>     x=1.1,
>>>     y=2.2,                     # <- This was copied from another_thing_config
>>>     z=3.0,
>>> )
```
