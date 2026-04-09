# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from typing import List, Union

from pconfigs.config import Config
from pconfigs.constructable import ConstructableConfig
from pconfigs.importing import getmoduleattr
from pconfigs.runner import ArgumentParser, Arguments, Namespace, Runnable, RunnableRunner, RunnerInfo


@dataclass
class RunnableConfig(Config):
    """A RunnableConfig is a dataclass that describes both the type of runner, and the config to use for that runner.
    This allows you to create config files that document both the code and the config settings that were used to drive
    that code. Using this class will allow you to use ConfigRunnableRunner, which prevents you from having to create
    separate command line arguments for the config file and the runner type when you call Runnable. Just use it.
    """

    runner_type: ConfigRunnable
    runner_config: Config


def get_runner_config(config: Union[RunnableConfig, ConstructableConfig]) -> Config:
    if isinstance(config, RunnableConfig):
        return config.runner_config
    elif isinstance(config, ConstructableConfig):
        return config
    else:
        raise ValueError(f"Unhandled config type: {type(config)}")


class ConfigRunnable(Runnable):
    """A ConfigRunnable is a Runnable whose constructor takes an argument named config that is of type Config."""

    @classmethod
    def make_argparser_args(cls, parser: ArgumentParser) -> ArgumentParser:
        parser.add_argument("--config", help="Import string to config object.", type=str, required=True)
        return parser

    @classmethod
    def make_constructor_args(cls, parsed_args: Namespace) -> Arguments:
        config = getmoduleattr(parsed_args.config)
        args = []
        kwargs = dict(config=config)
        return args, kwargs

    def main(self, parsed_args: Namespace, other_args: List[str]) -> int:
        raise NotImplementedError


class ConfigRunnableRunner(RunnableRunner):
    @classmethod
    def valid_argv(cls, argv: List[str]) -> bool:
        obj = getmoduleattr(sys.argv[1])

        check1 = isinstance(obj, RunnableConfig)
        check2 = isinstance(obj, ConstructableConfig) and issubclass(obj.constructable_type, ConfigRunnable)
        valid = check1 or check2

        module_dotpath ='.'.join(sys.argv[1].split('.')[:-1])
        module = importlib.import_module(module_dotpath)
        if hasattr(module, 'Pin'):
            raise RuntimeError(f"Pins cannot be used in config instances. Found Pin in {module_dotpath}")
        
        return valid

    def get_runner_and_args(self) -> RunnerInfo:
        runnable_config = getmoduleattr(sys.argv[1])
        runner_name = sys.argv[1]
        if isinstance(runnable_config, ConstructableConfig):
            runner_type = runnable_config.constructable_type
        elif isinstance(runnable_config, RunnableConfig):
            runner_type = runnable_config.runner_type
        else:
            msg = "Config type is neither ConstructableConfig nor ConfigRunnable: {}".format(type(runnable_config))
            raise RuntimeError(msg)

        # if not hasattr(runner_type, '_is_config_runnable'):
        if not issubclass(runner_type, ConfigRunnable):
            raise RuntimeError("Not a ConfigRunnable class: {}".format(runner_type))

        # Redirect the config argument to the actual config object for the ConfigRunnable class, and add --config param
        if isinstance(runnable_config, RunnableConfig):
            runner_config = runner_name + ".runner_config"

        elif isinstance(runnable_config, ConstructableConfig):
            runner_config = runner_name
        else:
            msg = "Config type is neither ConfigRunnable nor ConstructableConfig: {}".format(type(runnable_config))
            raise RuntimeError(msg)

        remaining_args = sys.argv[2:]
        if "--config" in remaining_args:
            raise RuntimeError("Cannot pass --config. It is is pre-specified as {}".format(runner_config))

        runner_argv = ["--config", runner_config] + remaining_args

        return RunnerInfo(runner_name, runner_type, runner_argv)
