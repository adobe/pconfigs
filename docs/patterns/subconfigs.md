# Subconfigs

Complex systems can be broken into submodules that are described by subconfigs. Consider the following example.

(subsec-define-a-system-with-submodules)=
## Define a system with submodules.
```python
from torch import nn, Tensor
from pconfigs import pconfiged, pconfig, pdefaults

# 1. Define a model to train
@pconfig(constructs=Model)
class ModelConfig:
    image_size: int       # Suppose the model needs the input size ahead of time.


# 2. Define a trainer that computes the loss for the model, etc.
@pconfig(constructs=Trainer)
class TrainerConfig:
    model_config: ModelConfig


# 3. Define a dataset for training
@pconfig(constructs=Dataset)
class DatasetConfig:
    image_size: int


# 4. Define a system that sets up everything for training.
@pconfig(constructs=System)
class SystemConfig:
    trainer_config: TrainerConfig
    dataset_config: DatasetConfig
```

Config systems like the one above allow for easy re-configuration. Consider the `System` class:
```python
@pconfiged(runnable=True)
class System:
    config: SystemConfig

    def __init__(self):
        self.trainer = self.config.trainer_config.construct()
        self.dataset = self.config.dataset_config.construct()
```
Because the `Model` and `Trainer` classes are fully described by their respective configs, the `System` class can construct them without concern for their parameter settings. Furthermore, users can create derived trainer and model classes, and the system will construct those without modification. 

Note that the design above simplifies common research practices. In deep learning research, for example, it is common for a class like `System` to have a config parameter that specifies (say) the dataset type as a string, and all parameters that are needed to construct the dataset. The `System` must then import all typenames that the user might request, and implement an `if`-`elif`-`else` block to construct every possible type with the associated constructor parameters for that type. In contrast, with `@pconfig`, that code is unecessary---`System` can construct any `Dataset` that the user wants. It's not the concern of the `System` to import the submodule types, or understand how to construct them; the submodules are responsible for that.


(subsec-tie-parameters-between-subconfigs)=
## Tie parameters between subconfigs.

Sometimes subconfigs of different types must share common parameters. For example, the `ModelConfig` and `DatasetConfig` above both have a `image_size` parameter. These should match for the `System` to function correctly. Systems naturally can manage such *tied properties* via `@pproperty`. Let's augment the `SystemConfig`:
```python
from pconfigs import pinputs, pproperty

@pconfig(constructs=System)
class SystemConfig:
    trainer_config: TrainerConfig
    dataset_config: DatasetConfig

    @pproperty
    def trainer_config(self) -> TrainerConfig:
        input_config = pinputs(self).trainer_config
        return TrainerConfig(
            input_config,
            model_config=ModelConfig(
                input_config.model_config,                    # The System ties the dataset
                image_size=self.dataset_config.image_size,    # ..and model configs together
            )
        )
```
In the above example, the user's input `ModelConfig` config is used via `pinputs()`, and the `image_size` is modified to ensure that it matches the `DatasetConfig`. This ensures the system will work. Note however,
1. If the user passes an `input_config` that specifies `ModelConfig.image_size`, they may not realize that it has no effect. This confusion can cause experimental errors.
1. If the user passes a derived kind of `ModelConfig` as input, the `SystemConfig` will replace that with an instance of the original type, `ModelConfig`.
1. The `@pproperty` code must specify all of the subconfig types to set a single parameter, `image_size`. This makes the code readable and interpretable by code editors, and also longer.

The above points are addressed in the sections below.

(subsec-pin-parameters-that-are-tied)=
## Pin parameters that are tied.

When parameters like `image_size` are shared between submodule configs, users should be notified which parameters will be overwritten by `@pproperty` logic. You can notify them by using the `Pinned` typehint (see also [Properties](../examples/properties))
```python
from pconfigs import pconfig, Pinned, Pin

@pconfig(constructs=Model)
class ModelConfig:
    image_size: Pinned[int]       # User cannot set image_size.


@pconfig(constructs=System)
class SystemConfig:
    @pproperty
    def trainer_config(self) -> TrainerConfig:
        # ...
                image_size=Pin(self.dataset_config.image_size),  # Use Pin to set the value.
        # ...
```
As shown above, modules that define config types can use `Pin` to set properties that are typehinted as `Pinned`. 

Users should not use `Pin` in config files (files which only specify config instances), and `pconfigs.run` will throw an error if a runnable config file imports `Pin`. Users will therefore receive an error if they mistakenly set a parameter that they cannot set. `Pinned` properties are also marked in printed config (along with their computed values), so users can identify the free parameters that they can set within the system.


(subsec-return-the-input-config-type)=
## Return the input config type.

Users can customize the system behavior by creating new, derived classes and config types. Property functions that tie parameters should respect this by reading the input type:
```python
from typing import Type

@pconfig(constructs=System)
class SystemConfig:
    trainer_config: TrainerConfig
    dataset_config: DatasetConfig

    @pproperty
    def trainer_config(self) -> TrainerConfig:
        input_config = pinputs(self).trainer_config
        InputConfig: Type[TrainerConfig] = type(input_config)   # Get the input TrainerType.

        return InputConfig(                          # Return an instance of the input type.
            input_config,
            model_config=ModelConfig(
                input_config.model_config,
                image_size=Pin(self.dataset_config.image_size),
            )
        )
```

(subsec-make-short-property-functions-with-psetter)=
## Make short property functions with psetter.

Property functions can become long when subconfig parameters are tied. In the example above, 9 lines of code are used to set `image_size`. This code is highly readable because code interpreters can jump to type definitions. This pattern can however be less helpful when `@pproperty` functions need to set parameter values in deeply nested config structures, like the one above. 

Use `psetter` to set deeply nested parameters in subconfigs:
```python
from pconfigs import psetter

@pconfig(constructs=System)
class SystemConfig:
    trainer_config: TrainerConfig
    dataset_config: DatasetConfig

    @pproperty
    def trainer_config(self) -> TrainerConfig:
        ps = psetter(
            type=TrainerConfig, 
            inputs=pinputs(self).trainer_config,
        )
        ps.model_config.image_size = Pin(self.dataset_config.image_size)

        return psetter(construct=ps)

```
By using `psetter`, you can succinctly implement the config nesting logic in the previous section. The user input types will be respected. Furthermore, an error will be thrown if any of the input subconfigs are not derived from the types that are hinted by `TrainerConfig`. 

Note that using `psetter` sacrificies some ability to jump to type definitions via the python interpreter. It is therefore recommended to use `psetter` only for deeply nested and complex config structures, where the readability of the `@pproperty` function is greatly improved. Shallow config structures will be more readable by following the code patterns in the previous sections.
