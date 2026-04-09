# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

import inspect
from pathlib import Path
from typing import Generic, TypeVar

from pconfigs.sentinel import Sentinel

T = TypeVar("T")


class TestSubdirs(Generic[T], metaclass=Sentinel):
    pass


class TestConfigsMeta(type):
    def __len__(cls):
        return len(cls.py_files)

    def __getitem__(cls, index):
        return cls.py_files[index]

    def __clear__(cls):
        cls.py_files = []


class TestConfigs(metaclass=TestConfigsMeta):
    py_files = []

    def __init__(self, *args):
        caller_dir = Path(inspect.stack()[1].filename).resolve().parent
        resolved_paths = []
        for a in args:
            path = Path(a)
            if not path.is_absolute():
                path = caller_dir / path

            if path.suffix != ".py":
                path = path.with_suffix(".py")

            resolved_paths.append(path.resolve())

        type(self).py_files = resolved_paths
