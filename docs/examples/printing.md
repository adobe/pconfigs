# Printing

Printing pconfigs produces documentation of how a system functions: the settings and the functions that are executed.

Suppose you have the following configured system.
```python
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
```
Configs can printed with `print()`, and their code can be generated using `repr()` as follows.

 (subsec-print-within-your-python-code)=
## Print within your python code.
```python
>>> config_str = str(system_config)          # Print only the config values.
>>> config_rep = repr(system_config)         # Also print the import paths.
```
The output of `repr()` is below.
```text
from pconfigs.examples.printing import SystemConfig, System
from pconfigs.examples.quickstart import ThingConfig, Thing

# NOTE: This code is not intended to run. It is for reading and looking up type definitions.
# If you want to run or inspect these objects, import the config from where it is defined.

SystemConfig(
    constructable_type=System,  # ClassVar (omit from config)
    mode="run",
    thing_config=ThingConfig(
        constructable_type=Thing,  # ClassVar (omit from config)
        x=1.0,
        y=2.0,
        z=3.0,
    ),
)
```
Note that the types are printed with their import paths. Printing pconfig `repr()` code therefore allows you to identify the settings and types that define the system.


 (subsec-print-from-the-command-line)=
## Print from the command line.

Config can be printed to a file for inspection, and to facilitate file diff comparisions. This prints the repr() by default.
```console
$ python -m pconfigs.print  pconfigs.examples.printing.system_config  >  config_print.py
```
This is particularly useful for debugging. Without running the system code, the printed config settings can be viewed alongside the code. The printed imports specify what code will be executed, and code indexers will jump-to-definition of the imports in the `config_print.py`. File difference tools can be used to compare pairs of printed configs to check for experimental changes or errors.