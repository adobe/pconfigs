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


# Define a class that contains config.
# • Constructor takes no arguments.
@pconfiged
class Thing:
    config: ThingConfig

    def __init__(self):
        pass

    def echo(self):
        print(self.config)  # Access config properties.


# Define a config for the class.
# • Configs are kept separate from the class.
@pconfig(constructs=Thing)
class ThingConfig:
    x: float
    y: float
    z: float


# Set default values for the config parameters.
# • Defaults are set separately to de-clutter config definitions.
pdefaults += ThingConfig(
    x=1.0,
    y=2.0,
    z=3.0,
)


# 1. Construct an instance of the config.
thing_config = ThingConfig()
# print(thing_config)

thing = thing_config.construct()  # Construct the pconfiged class.
# thing.echo()  # Same output as above.


# 2. Construct a non-default instance of the config.
another_thing_config = ThingConfig(y=2.2)
# print(another_thing_config)


# 3. Auto-copy between configs
last_thing_config = ThingConfig(
    another_thing_config,
    x=1.1,
)
# print(last_thing_config)
