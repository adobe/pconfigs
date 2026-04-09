# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

import subprocess
import sys


def _run_command_and_capture_error_output() -> str:
    command_args = [sys.executable, "-m", "pconfigs.run", "tests.t042_helpers.instance.config"]
    completed_process = subprocess.run(command_args, capture_output=True, text=True)
    return completed_process.stderr or ""


def test_command_produces_error_output_string() -> None:
    error_output = _run_command_and_capture_error_output().strip()
    if not isinstance(error_output, str):
        raise RuntimeError("Expected the command to produce an error output string on stderr.")

    msg = "RuntimeError: Pins cannot be used in config instances."
    if not msg in error_output:
        raise RuntimeError(f"Expected the command to produce an error, '{msg}'")


test_command_produces_error_output_string()
