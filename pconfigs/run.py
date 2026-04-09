# Copyright 2026 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

import sys

from pconfigs.config_runner import ConfigRunnableRunner
from pconfigs.importing import getmoduleattr


class RunnerDispatch:
    def __init__(self):
        # Try to get the attribute. All runners require that the first parameter be some of attribute in a module.
        getmoduleattr(sys.argv[1])

    def main(self):
        retcode = 0
        if ConfigRunnableRunner.valid_argv(sys.argv):
            # ConfigRunnables are runnables that are constructed with a Config object to document how they are run.
            retcode = ConfigRunnableRunner().main()

        exit(retcode)


if __name__ == "__main__":
    RunnerDispatch().main()
