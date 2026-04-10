# Environments

Systems that depend upon the runtime environment (e.g., GPUs, local file paths) can be configured with environment config.

 (subsec-use-penv-to-declare-environment-variables)=
## Use `@penv` to declare environment variables.

```python
from pconfigs import pconfig, pdefaults, penv

@penv(convention="uppercase")
class TrainerEnv:
    world_size: int
    rank: int


@pconfig
class TrainerConfig:
    environment: TrainerEnv  # Environments are always called 'environment'
    print_frequency_steps: int


trainer_config = TrainerConfig(
    print_frequency_steps=10,
)
```

```console
$ python -m pconfigs.print pconfigs.examples.environments.main.trainer_config
RuntimeError: Environment value for 'world_size' is not set.

$ WORLD_SIZE=8 RANK=0 python -m pconfigs.print pconfigs.examples.environments.main.trainer_config
TrainerConfig(
    environment=TrainerEnv(  # ClassVar (omit from config)
        WORLD_SIZE="8",
        RANK="0",
    ),
    print_frequency_steps=10,
)
```

 (subsec-set-default-values-for-optional-environment-variables)=
## Set default values for optional environment variables.
```python
@penv(convention="uppercase")
class WithDefaultsTrainerEnv(TrainerEnv):
    world_size: int = 1
    rank: int = 0


@pconfig
class WithDefaultsTrainerConfig(TrainerConfig):
    environment: WithDefaultsTrainerEnv  # Environments are always called 'environment'


trainer_config = WithDefaultsTrainerConfig(
    print_frequency_steps=10,
)
```

```console
$ python -m pconfigs.print pconfigs.examples.environments.defaults.trainer_config
WithDefaultsTrainerConfig(
    environment=WithDefaultsTrainerEnv(  # ClassVar (omit from config)
        WORLD_SIZE="1",
        RANK="0",
    ),
    print_frequency_steps=10,
)
```

 (subsec-environment-variable-types-are-auto-cast)=
## Environment variable types are auto-cast.
```python
from pconfigs import pconfiged

@pconfiged
class MyTrainer:
    config: MyTrainerConfig

    def is_root(self) -> bool:
        return self.config.environment.rank == 0


@pconfig(constructs=MyTrainer)
class MyTrainerConfig(TrainerConfig):
    pass


my_trainer_config = MyTrainerConfig(
    print_frequency_steps=10,
)

my_trainer = my_trainer_config.construct()
print("Is root:", my_trainer.is_root())
```

```console
$ RANK=0 WORLD_SIZE=8 python -m pconfigs.examples.environments.types
Is root: True

$ RANK=1 WORLD_SIZE=8 python -m pconfigs.examples.environments.types
Is root: False
```
