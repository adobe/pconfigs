# Testing

You can test pconfigs using `pytest` or `python`. Consider the following project.

 (subsec-setup-a-project)=
## Setup a project.
```text
my_project/
    source/
        __init__.py
        modules/                   # Modules define pconfig types, classes, and defaults.
            __init__.py
            trainer.py
            model.py

        pconfigs/                  # Config directories define system configurations.
            __pconfigs__.py        # A sentinel file marks a directory of pconfigs.
            experiment_1.py        # Files only contain config instances.
            experiment_2.py

            subdir/
                __pconfigs__.py    # Optional (see below).
                sub_expr_1.py
                sub_expr_2.py

    docs/                          # Etc.
```

Config files like `pconfigs/experiment_1.py` specify config instances. For example,
```python
from source.modules.trainer import TrainerConfig

config = TrainerConfig(
    message="Hello, World!",
) 
```
And this config might run your first experiment,
```console
$ python -m pconfigs.run source.pconfigs.experiment_1.config
```

 (subsec-test-pconfig-files)=
## Test pconfig files.

Config files usually contain computed `@pproperty` fields that should not break as the configs are developed. You can test configs as follows.

```console
~/my_project$ ptest
```
which is installed with the `pconfigs` package. This command calls `pytest` with arguments that minimize the output. Alternativelly, `pytest` can be run manually with
```console
~/my_project$ pytest --pyargs pconfigs.test
```
Both invocations will run the same tests: all `.py` files in directories that contain a `__pconfigs__.py` sentinel file will be evaluated. This validates that all `@pproperties` run without error.


 (subsec-test-all-subdirectories)=
## Test all subdirectories.

You can test all configs in a subdirectory tree as follows.

Modify `__pconfigs__.py`:
```python
from pconfigs import TestSubdirs
```
By importing the `TestSubdirs` sentinel, `pconfigs.test` will test all `.py` config files in all subdirectories regardless of whether the subdirectory contains a `__pconfigs__.py` file.

 (subsec-test-specific-pconfigs)=
## Test specific pconfigs.

The pconfig testing system is designed to be low maintenance: as new configs are added, or config filenames are changed, running `pconfigs.test` will continue to test all configs that are marked with the `__pconfigs__.py` sentinel file; no development work is required to update tests. Nonetheless, if you find that it is necessary to specify that only specific configs in a directory are tested, you can do so as follows.

To test specific configs, modify `__pconfigs__.py`:
```python
from pconfigs import TestSubdirs, TestManually

TestManually(
    "experiment_1",                    # List only the modules that you want to test.
)
```
The above file will test only `experiment_1.py` in the current directory. Subdirectory configs `sub_expr_1.py` and `sub_expr_2.py` will also be tested because `TestSubdirs` is imported.
