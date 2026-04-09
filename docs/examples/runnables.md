# Running


 (subsec-configure-a-runnable-class)=
## Configure a runnable class.
```python
from pconfigs import pconfig, pconfiged

@pconfiged(runnable=True)
class Main:
    config: MainConfig

    def main(self, *args, **kwargs):
        print(self.config.message)


@pconfig(constructs=Main)
class MainConfig:
    message: str


main_config = MainConfig(
    message="Hello, world!",
)
```
Now you can do,
```console
$ python -m pconfigs.run dot.path.to.main_config
Hello, world!
```

Runnable configs also allow you to control the argument parser, but arguments are an anti-pattern in pconfig'd systems. Argument parsing is therefore not covered here.
