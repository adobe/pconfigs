# pconfigs

**A Python library for reproducible research.**

Most ML codebases are split into experiment code, main scripts, and config text files. As the codebase evolves, the experiment and main script code change, the config text drifts out of sync, and results become difficult to reproduce. New experiments can also be difficult to implement because the main script must anticipate future experiments; when the main script cannot express the next experiment, large parts of the system must be rewritten. In practice, rewrites are postponed with an unsustainable patchwork of defaults, overrides, and options. Meanwhile, config text is scattered across external file systems or servers, and the truth of what will run becomes difficult for humans and agents to infer. `pconfigs` solves these problems by replacing config text with Python config files that live in the repo alongside the code, and fully specify the experiment, main, and config together — they can be executed, constructed, printed to reveal the fully resolved configuration of every submodule, and tested to ensure they stay valid as the codebase evolves.

**[Documentation](https://opensource.adobe.com/pconfigs/)**

## Installation
```
pip install pconfigs
```

## Example

```python
from __future__ import annotations

from pconfigs import pconfig, pconfiged

@pconfiged(runnable=True)                # Runnable means this class will have a main().
class Trainer:
    config: TrainerConfig                # Typehint the config type for the class.

    def main(self, *args, **kwargs):
        print(self.config.message)       # The config is available at runtime.


@pconfig(constructs=Trainer)             # This config constructs a Trainer class.
class TrainerConfig:
    message: str                         # All config parameters are typehinted.
    lr: float


config = TrainerConfig(                  # Create an experiment.
    message="Hello, World!",
    lr=1e-5,
)
```

Run an experiment:
```console
$ python -m pconfigs.run base.experiment.config
```

Derive a new experiment from an existing one:
```python
from base.experiment import config as base

config = TrainerConfig(
    base,      # Auto-copy all parameters from base.
    lr=1e-4,   # Change only the learning rate.
)
```

Print the fully resolved config as Python code:
```console
$ python -m pconfigs.print new.experiment.config > printed_config.py
```

See the [quickstart](https://adobe.github.io/pconfigs/introduction/quickstart.html) for a complete walkthrough.

### Contributing

Contributions are welcomed! Read the [Contributing Guide](https://github.com/adobe/pconfigs/blob/main/.github/CONTRIBUTING.md) for more information.

### Licensing

This project is licensed under the Apache V2 License. See [LICENSE](LICENSE) for more information.
