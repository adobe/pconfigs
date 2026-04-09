# 🌲 <span class="brand-name">pconfigs</span>

:::{rubric} A Python library for research and flexible system design.<br><span class="subtitle-small">&nbsp;&nbsp;Reproducible &nbsp;•&nbsp; Extensible &nbsp;•&nbsp; Readable &nbsp;•&nbsp; Maintainable</span>
:class: subtitle
:::
<div class="poem-container">
<p class="poem">
A learning rate too high, a network loss explodes;<br>
A typo in a path, some data never loads.<br>
Defaults in depths overridden, propagated endlessly downstream;<br>
<!-- Defaults in depths overridden, cascaded endlessly downstream;  -->
Ten thousand lines of config, yet most are never seen.<br>
So pconfig. Print the truth! Nothing is as it seems...
</p>
</div>

:::{rubric} Why pconfigs?
:class: section-caption
:::

<div class="justify">

<span class="drop-cap">M</span>achine learning researchers share many common coding frustrations, including a sadly poetic struggle against code whose actual runtime behavior is opaque even to modern coding agents. These frustrations stem from a central, structural problem: in most codebases, there are three separate components: (a) experiment code, (b) driver code that runs experiments, and (c) a config text file that the driver reads to determine which experiment code to execute and with what parameter values. This split is historically conventional, but it becomes problematic as the codebase evolves: the experiment and driver code change, the config text drifts out of sync, and results become difficult to reproduce. New experiments can also be difficult to implement because the driver must anticipate future experiments; when the driver cannot express the next experiment, large parts of the system must be rewritten. In practice, rewrites are postponed with an unsustainable patchwork of defaults, overrides, and options. Meanwhile, config text is scattered across external file systems or servers, and the truth of what will run becomes difficult for humans and agents to infer.

The pconfigs library replaces config text files with a Python config file that lives in the same repository as the code. These pconfig files are ordinary Python code, so they can be maintained alongside the codebase as it evolves. A pconfig file specifies which experiment code to execute and which driver runs it, and includes every parameter that is needed. This design eliminates the failure modes of config text files: the config does not drift away from the experiment/driver, ephemeral command-line values are not used and forgotten, and novel systems can be created (without breaking prior experiments) as pconfig files that reference new experiment code, driver code, and parameters. pconfigs are therefore **executable**: you run an experiment by running its pconfig.

Experiments naturally involve constructing submodules (with constructor parameters) and calling subfunctions (with call parameters); in most codebases, the caller must pass configuration values to these objects and functions. With pconfigs, these submodules and subfunctions are specified within the experiment pconfig as sub-pconfigs. Since pconfig objects can specify both the class or function and its config parameters, pconfig objects are **constructible** and **callable**: they can be used without passing configuration in the caller—even when parameters must be computed from other settings. This invoke-without-parameters design pattern makes experiments highly reconfigurable: modules and functions are customized or swapped by changing the pconfig rather than the caller code. Applied recursively, this pattern allows the pconfig for an experiment to capture the fully resolved configuration of every subfunction and submodule. We can therefore **print** pconfigs to reveal the entire system configuration as readable Python code before execution, while experiments are being implemented.


In summary, pconfigs provide a way to create python code files that describe experiments, modules, and functions explicitly and completely: they can be **executed**, **constructed**, and **called** without parameters, **printed** to reveal the fully resolved configuration of all submodules and functions as readable Python code, and **tested** to ensure they remain valid as the codebase evolves. The truth of what will run therefore becomes transparent to both humans and agents, and experiments can be indefinitely preserved, reproduced, and specialized over time. 


<!-- OLD LONG VERSION
<span class="drop-cap">M</span>achine learning researchers share many common coding frustrations, including a sadly poetic struggle against code whose actual runtime behavior is opaque even to modern coding agents. These frustrations stem from a central, structural problem: in most codebases, there are three separate components: (a) experiment code, (b) driver code that runs experiments, and (c) a config text file that the driver reads to determine which experiment code to execute and with what parameter values. This split is historically conventional, but it becomes problematic as the codebase evolves: the experiment and driver code changes, the config text drifts out of sync, and results become difficult to reproduce. New experiments can also be difficult to implement because the driver must anticipate future experiments; when the driver cannot express the next experiment, large parts of the system must be rewritten. In practice, rewrites are postponed with an unsustainable patchwork of defaults, overrides, and options. Meanwhile, config text is scattered across external file systems or servers, and the truth of what will run becomes difficult for humans and agents to infer.

The pconfigs library replaces config text files with a Python config file that lives in the same repository as the code. These pconfig files are ordinary Python code, so they can be maintained alongside the codebase as it evolves. A pconfig file specifies which experiment code to execute and which driver runs it, and includes every parameter that is needed. This design eliminates the failure modes of config text files: the config does not drift away from the experiment/driver, ephemeral command-line values are not used and forgotten, and novel systems can easily be created—without breaking prior experiments—as pconfig files that reference new experiment code, driver code, and parameters. This encapsulation makes pconfig files executable without command-line parameters.

When an experiment runs, the driver constructs submodules (with constructor parameters) and calls subfunctions (with call parameters); in most codebases, these introduce hidden configuration that includes values computed from other settings. With pconfigs, submodules and subfunctions can be pconfigured too, so they can be constructed or called without passing ad-hoc parameters at each call site. This makes the experiment and driver code highly reconfigurable: the configuration settings of a submodule or subfunction are not the concern of the code that uses it, so submodules and subfunctions can be swapped without changing the caller. Applied recursively, this means the pconfig for an experiment captures the fully resolved configuration settings of every subfunction and submodule. This full encapsulation makes the entire system configuration printable as readable Python code—revealing runtime settings before execution, while experiments are still being implemented.

In summary, pconfigs provide a way to write python code that describes experiments explicitly and completely. By maintaining these descriptions, experimental designs can be preserved and specialized over time. The pconfigs library additionally supports computed configuration values, a method to create new experiments from prior ones, and automated tests that ensure that a tree of pconfig files does not break as the codebase is refactored, among many other features.
-->

<!-- OLD SHORT VERSION
achine learning researchers share many common coding frustrations, including a sadly poetic struggle against code whose actual runtime behavior is opaque even to modern coding agents. These frustrations stem from a central, structural problem: in most codebases, there are three separate components: (a) experiment code, (b) driver code that runs experiments, and (c) a config text file that the driver reads to determine which experiment code to execute and with what parameter values. This split is historically conventional, but it becomes problematic as the codebase evolves: the experiment and driver code changes, the config text drifts out of sync, and results become difficult to reproduce. New experiments can also be difficult to implement because the driver must anticipate future experiments; when the driver cannot express the next experiment, large parts of the system must be rewritten. In practice, rewrites are postponed with an unsustainable patchwork of defaults, overrides, and options. Meanwhile, config text is scattered across external file systems or servers, and the truth of what will run becomes difficult for humans and agents to infer.

The pconfigs library replaces config text files with a Python config file that lives in the same repository as the code. These pconfig files are ordinary Python code, so they can be maintained alongside the codebase as it evolves. A pconfig file specifies which experiment code to execute and which driver runs it, and it can include every parameter needed to execute an experiment, so results do not depend on ephemeral command-line values. This design eliminates the failure modes of config text files: the config does not drift away from the experiment/driver, ephemeral command-line values are not used and forgotten, novel systems can easily be created as new experiment or driver code without breaking prior experiments, and the construction parameters of every submodule can be resolved and printed as Python code — revealing historically inaccessible runtime settings while experiments are implemented.

In summary, pconfigs provide a way to write python code that describes experiments explicitly and completely. By maintaining these descriptions, experimental designs can be preserved and specialized over time. The pconfigs library additionally supports computed configuration values, a method to create new experiments from prior ones, and automated tests that ensure that a tree of pconfig files does not break as the codebase is refactored, among many other features.
-->



</div>

## Example

```python
from __future__ import annotations

from pconfigs import pconfig, pconfiged

@pconfiged(runnable=True)                # Runnable means this class will have a main().
class Trainer:
    config: TrainerConfig                # Typehint the config type for the class.

    def __init__(self):                  # The constructor takes no parameters.
        pass

    def main(self, *args, **kwargs):     
        print(self.config.message)       # The config is available at runtime.


@pconfig(constructs=Trainer)             # This config constructs a Trainer class.
class TrainerConfig:
    message: str                         # All config parameters are typehinted.
    lr: float                            # (not shown) computed values can also be defined.


config = TrainerConfig(                  # Create an experiment.
    message="Hello, World!",
    lr=1e-5,
)
```
Run an experiment:
```console
$ python -m  pconfigs.run  base.experiment.config
              ––––––––––    –––––––––––––   ––––
                runner         module         attribute within the module
```
Make a new experiment:
```python
from base.experiment import config as base

config = TrainerConfig(
    base,      # Auto-copy all parameters from base.
    lr=1e-4,   # Change only the learning rate. 
)
```
Print your experiment configs as complete and interpretable python code:
```console
$ python -m  pconfigs.print  new.experiment.config  >  printed_config_new.py
              ––––––––––––
                 printer
```
Read your printed experiment config in your Python editor:
![Alt text for the image](printed_config_annotated.png)

Compare your experiments with `cursor` or `vscode`:
```
$ cursor --diff  printed_config_base.py  printed_config_new.py
```
Test all experiment configs in your repository. This imports each config to verify that computed properties are not broken.
```
$ ptest      # <-- Automatically find and import all pconfig instances in your repository.
........................................                               [100%]
40 passed, 14 warnings in 14.67s
```


```{toctree}
:caption: Introduction
:maxdepth: 2
:numbered: 2
introduction/about
introduction/setup
introduction/quickstart
introduction/versions
```

```{toctree}
:caption: Examples
:maxdepth: 2
:numbered: 2
examples/about
examples/construction
examples/runnables
examples/printing
examples/environments
examples/properties
examples/testing
examples/enums
```

```{toctree}
:caption: External Libraries
:maxdepth: 2
:numbered: 2
external_libraries/about
external_libraries/functions
external_libraries/classes
```

```{toctree}
:caption: Design Patterns
:maxdepth: 2
:numbered: 2
patterns/about
patterns/subconfigs
patterns/claude
patterns/cursor
```

```{toctree}
:caption: Comparisons
:maxdepth: 2
:numbered: 2
comparisons/about
comparisons/pconfigs
comparisons/gin
comparisons/hydra
```

```{toctree}
:caption: API
:maxdepth: 2
<!-- :numbered: 2 -->
api/index
```
