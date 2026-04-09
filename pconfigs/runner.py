# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

import sys
from argparse import ArgumentParser, Namespace
from copy import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from pconfigs.environment import EnvironmentBase
from pconfigs.importing import getmoduleattr

# The general form that all function arguments take: *args, **kwargs
Args = List
Kwargs = Dict
Arguments = Tuple[Args, Kwargs]


class Runnable:
    environment: EnvironmentBase

    @classmethod
    def make_arg_parser(cls) -> ArgumentParser:
        return ArgumentParser()

    @classmethod
    def make_argparser_args(cls, parser: ArgumentParser) -> ArgumentParser:
        return parser

    @classmethod
    def make_constructor_args(cls, parsed_args: Namespace) -> Arguments:
        return [], {}

    def main(self, parsed_args: Namespace, other_args: List[str]) -> int:
        return 0


@dataclass
class RunnerInfo:
    name: str
    type: Runnable
    argv: List[str]


class RunnableRunner:
    @classmethod
    def valid_argv(cls, argv: List[str]) -> bool:
        obj = getmoduleattr(sys.argv[1])
        if not issubclass(obj, Runnable):
            return False

        return True

    def get_runner_name(self) -> str:
        return sys.argv[1]

    def get_runner_and_args(self) -> RunnerInfo:
        runner_name = self.get_runner_name()
        runner_type = getmoduleattr(runner_name)
        if not issubclass(runner_type, Runnable):
            raise RuntimeError("Class is not runnable: {}".format(runner_type))

        runner_argv = sys.argv[2:]

        return RunnerInfo(runner_name, runner_type, runner_argv)

    def parse_args(self, runner_info: RunnerInfo) -> Tuple[Namespace, List[str]]:
        parser = runner_info.type.make_arg_parser()
        parser = runner_info.type.make_argparser_args(parser)
        parser.prog = runner_info.name  # specify the module name when they pass --help
        return parser.parse_known_args(runner_info.argv)

    def run_runner(self, runner_info: RunnerInfo) -> int:
        args, others = self.parse_args(runner_info)
        args_c, kwargs_c = runner_info.type.make_constructor_args(args)
        runner = runner_info.type(*args_c, **kwargs_c)
        return runner.main(args, others)

    def main(self) -> int:
        runner_info = self.get_runner_and_args()
        return self.run_runner(runner_info)
