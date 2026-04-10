# Functions

Functions can be configured using a variety of `pconfig` tools.

(subsec-configure-a-function)=
## Configure a function

Make `source/modules/line_func.py`
```python
from pconfigs.pinnable import pconfig
from external_library import line_func

## This function is imported from an external library that we cannot modify.
#
# def line_func(x: float, slope: float = 1.0, offset: float = 0.0) -> float:
#     return x * slope + offset
#

@pconfig(calls=line_func)              # This config calls line_func()
class LineFunc:                        # Use suffix 'Func' because this class is callable!
    pass                               # Params, typehints, and defaults are auto generated.
```
The default `LineFunc` is automatically set:
```python
>>> from source.modules.line_func import LineFunc
>>> print(pdefaults(LineFunc))
LineFunc(
    funcname=external_library.line_func,  # ClassVar (omit from config)
    slope=1.0,
    offset=0.0,
)
```
Notice that the required function parameter `x: float` is not included in the printed config for `LineFunc`. `@pconfig` creates config parameters only for function arguments that have a default value. 

We are free to change the function defaults, so let's add to `source/modules/line_func.py`,
```python
pdefaults += LineFunc(
    slope=2.0,                            # Only the default slope is changed.
)
```
The default config is updated accordingly. Configuring external functions therefore allows us to reconfigure and document the parameters that functions require.

(subsec-use-configured-functions)=
## Use configured functions

Let's take this example further by making a line plotting tool. Make `source/modules/line_plotter.py`
```python
from source.modules.line_func import LineFunc
from pconfigs import pdefaults, pconfig, pconfiged

@pconfiged(runnable=True)
class LinePlotter:
    config: LinePlotterConfig

    def main(self, *args, **kwargs):
        x = range(self.config.x_lo, self.config.x_hi)
        y = [
            self.config.line_func(x=c)   # Calls external_library.line_func().
            for c in x                   #  ..with configured slope & offset.
        ]
        self.plot(x, y)


@pconfig(constructs=LinePlotter)
class LinePlotterConfig:
    line_func: LineFunc
    x_lo: int
    x_hi: int


pdefaults += LinePlotterConfig(
    line_func=pdefaults(LineFunc),
    x_lo=-10,
    x_hi=10,
)
```
Now we can configure and document any line plotter system. 

Make `source/pconfig/line_experiment.py`
```python
from source.modules.line_plotter import LinePlotter
from sourcs.modules.line_func import LineFunc

config = LinePlotter(
    line_func=LineFunc(
        slope=4.0, 
    )
)
```
The parameters of this particular line and its plotting process can now be printed and run.
```bash
$ python -m pconfigs.print source.pconfig.line_experiment.config
$ python -m pconfigs.run   source.pconfig.line_experiment.config
```
