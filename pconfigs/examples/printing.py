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
from pconfigs.examples.quickstart import ThingConfig


@pconfiged
class System:
    config: SystemConfig

    def run(self):
        print(self.config.mode)
        print(self.config.thing_config)


@pconfig(constructs=System)
class SystemConfig:
    mode: str
    thing_config: ThingConfig



system_config = SystemConfig(
    mode="run",
    thing_config=pdefaults(ThingConfig),
)
