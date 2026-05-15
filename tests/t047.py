# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

import argparse
import os

from pconfigs.config_runner import ConfigRunnable


parser = argparse.ArgumentParser()
ConfigRunnable.make_argparser_args(parser)

breakpoint()

help_text = parser.format_help()
assert "--config" not in help_text, (
    "--config must not appear in the help output of a ConfigRunnable. "
    f"Got:\n{help_text}"
)

print(f"{os.path.basename(__file__)}  --config is suppressed from ConfigRunnable help output.")
