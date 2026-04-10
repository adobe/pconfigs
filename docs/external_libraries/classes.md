# Classes

External classes can be configured using `pconfigs`, often with just 2-3 lines of pconfig code. Configurable classes are classes whose optional constructor parameters are simple types (e.g., string, int, etc). 

Note that some external classes follow design patterns that cannot be configured. One example is the Pytorch Lightning [Trainer](https://github.com/Lightning-AI/pytorch-lightning/blob/b15d394f2a9d36ccefba08328ac8dc2bd13e49b2/src/lightning/pytorch/trainer/trainer.py#L91-L135) class. As of this writing, its constructor accepts 41 optional parameters, many of which are complex types like `callbacks`---these values cannot be printed as simple plaintext values. To configure such non-configurable classes, one must make a derived class whose constructor accepts only simply-typed parameters; the parent type is then constructed from the simply typed input parameters.

(subsec-configure-an-external-class)=
## Configure an external class

Make `source/modules/mock_class.py`
```python
from pconfigs.pinnable import pconfig
from external_library import KwargedClass

# Suppose the following class is imported from an external library that we cannot modify.
#
# class KwargedClass:
#     def __init__(self, x: float, param_a: float = 1.0, param_b: float = 2.0):
#         self.x = x
#         self.param_a = param_a
#         self.param_b = param_b

@pconfig(mocks=KwargedClass)
class KwargedClassConfig:
    pass


kwarged_class_config = KwargedClassConfig()
```
The default config values are automatically read from the external library:
```console
>>> print(kwarged_class_config)
KwargedClassConfig(
    constructable_type=KwargedClass,  # ClassVar (omit from config)
    param_a=1.0,
    param_b=2.0,
)
```
Instances of `KwargedClass` can be created as follows
```python
kwarged_class = kwarged_class_config.construct(x=100)    # variable name is required.
```
Config parameters are automatically passed to the constructor for you.


(subsec-extend-an-external-class)=
## Extend an external class

External classes can be configured and extended as follows.

Make `source/modules/extended_class.py`
```python
from external_library import KwargedClass
from pconfigs.pinnable import pconfig, pconfiged

@pconfiged(mock=True)
class DerivedClass(KwargedClass):
    config: DerivedClassConfig

    def forward(self):
        print(f"Custom config value: y={self.config.y}")


@pconfig(constructs=DerivedClass)
class DerivedClassConfig:
    y: int


derived_class_config = DerivedClassConfig(
    y=10,
)
```
Methods in the derived class can now access new config parameters:
```python
>>> derived_class = derived_class_config.construct(x=100)
>>> derived_class.forward()
Custom config value: y=10
```