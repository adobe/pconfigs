# Quickstart

`pconfigs` is a generic library for configuring complex systems. Here we'll create a hypothetical trainer for a machine learning model.

(subsec-setup-claude)=
## Setup AI agent rules.

Install pconfigs rules for your AI coding agent:

- **Claude**: `python -m pconfigs.claude install` (see [Claude Integration](../patterns/claude))
- **Cursor**: `python -m pconfigs.cursor install` (see [Cursor Integration](../patterns/cursor))

Then ask the agent to `Create a new runnable pconfigs example module + config file.`

(subsec-configure-a-class)=
## Configure a class.

Create `source/modules/trainer.py` within your project.
```python
from __future__ import annotations            # Forward references of typehints are required.
from pconfigs import pconfig, pconfiged, pdefaults

# Trainer class
@pconfiged(runnable=True)                     # runnable=True facilitates a main().
class Trainer:
    config: TrainerConfig                     # A class' config is always called 'config'.

    def __init__(self):                       # Constructor takes no arguments.
        pass

    def main(self, *args, **kwargs):                
        print(self.config.message)            # Config is automatically available.
        print(f"Lr: {self.config.lr}")


# Trainer config class.
@pconfig(constructs=Trainer)                  # We can use this config to construct Trainer.
class TrainerConfig:
    message: str                              # All config parameters are typehinted.
    lr: float


# Config defaults.
pdefaults += TrainerConfig(                   # Set defaults separately from type 
    message="Hello, World!",                  #  ..definitions (avoids clutter).
    lr=1e-4,
)
```

 (subsec-create-a-config-file)=
## Create a config file.

Make `source/pconfig/experiment_1.py`:
```python
from source.modules.trainer import TrainerConfig

config = TrainerConfig(                       # Set just the learning rate. Use defaults
    lr=1e-3,                                  #  ..for the other config parameters.
)                                   
```

 (subsec-run-the-configured-system)=
## Run the configured system.
```bash
$ python -m  pconfigs.run  source.pconfig.experiment_1.config
              ––––––––––    –––––––––––––––––––––––––   ––––
                runner               dotpath             attribute
```
This command constructs `Trainer` with the config in `experiment_1.py` and runs `Trainer.main()`. Specifically, it 

1. Reads the `TrainerConfig` instance in `experiment_1.py`
1. Reads the constructable type that has been associated with `TrainerConfig` (it's `Trainer`)
1. Checks if `Trainer` is runnable (it is, because `runnable=True`),
1. Constructs `Trainer` with `experiment_1.config`, and
1. Calls `main()`.

The output is,
```text
Hello, World!
Lr: 0.001
```
This works equally well in machine learning applications, for example
```bash
$ torchrun --nproc_per_node=1 -m pconfigs.run source.pconfig.experiment_1.config
```

Runnable configs can encapsulate all system parameters into a single executable command that takes no parameters. This encapsulation facilitates reproducible experiments.


 (subsec-create-a-revised-config-file)=
## Create a revised config file.

A second feature of pconfigs is that you can automatically copy parameters between them.

Make `source/pconfig/experiment_2.py`:
```python
from source.modules.trainer import TrainerConfig
from source.pconfig.experiment_1 import config as base 

config = TrainerConfig(
    base,                                    # Copy all parameters from the base experiment.
    message="Experiment 2.",                 # ..except change the message parameter.
)
```
This automatic copying capability simplifies the process of creating subsequent experiments. (See also [Construction](../examples/construction).)
```bash
$ python -m  pconfigs.run  source.pconfig.experiment_2.config
```
prints
```text
Experiment 2.
Lr: 0.001
```

 (subsec-print-and-compare-configs)=
## Print and compare configs.

A third feature of pconfigs is printing, which documents all parameter values and the paths of all types that define the system.

```bash
$ python -m pconfigs.print  source.pconfig.experiment_2.config
             –––––––––––                                 ––––
               printer                                    prints repr(config)
```
This command prints interpretable python code, formatted with [Black](https://black.readthedocs.io/en/stable/), as shown below. (See also [Printing](../examples/printing).)
```text
from source.modules.trainer import TrainerConfig, Trainer

# NOTE: This code is not intended to run. It is for reading and looking up type definitions.
# If you want to run or inspect these objects, import the config from where it is defined.

TrainerConfig(
    constructable_type=Trainer,  # ClassVar (omit from config)
    message="Hello, World!",
    lr=0.001,
)
```
You can 

1. Use the printed import paths and typenames to identify the relevant source code in your project,
1. Use file diff tools to compare printed configs between experiments.

*NOTE: `constructable_type=Trainer` is not a string `='Trainer'`. The config contains the resolved python typename, which unambiguously defines the module in which the code is defined. You do not need to manually create model registries that map strings like `'Trainer'` to the resolved typename (a common practice in deep learning codebases). The Python language interpreter does this already.*

You can also print within your code. This enables you to log the system configuration when experiments are launched.
```python
>>> from source.pconfig.experiment_2 import config
>>> print(config)                  # Prints only the config values.
>>> print(repr(config))            # Prints also with import paths, as with pconfigs.print.
```

 (subsec-but-wait-theres-more)=
## But wait, there's more!

This quickstart covers the essentials: defining, running, copying, and printing configs. For more details,

1. Constructing configs (see [Construction](../examples/construction))
1. Running configs (see [Runnables](../examples/runnables)) 
1. Printing configs (see [Printing](../examples/printing))

And many important `pconfig` features have not been covered here:

1. Computed properties with `@pproperty` (see [Properties](../examples/properties))
1. Environment variables with `@penv` (see [Environments](../examples/environments))
1. Testing with `pconfigs.test` (see [Testing](../examples/testing))
1. External library configuration with `@pconfiged(mock=True)` (see [External Libraries](../examples/mock))
1. Interpretable enum representations with `@penum` (see [Enums](../examples/enums))

