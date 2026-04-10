# Enums

Printed pconfigs are interpretable python code, provided that the printed representation of all parameter values can be interpreted as python code. Python Enums are one case for which the default python representation (repr) cannot be interpreted as python code.

(subsec-use-penum-to-print-interpretable-enum-values)=
## Use `@penum` to print interpretable Enum values.

```python
from pconfigs.pinnable import penum

@penum
class Color:
    red = "red"
    blue = "blue"
```
The printed enum representation can be interpreted:
```python
>>> print(repr(Color.red))
Color.red
```
whereas a typical python Enum would print `<Color.red: 'red'>`, which cannot be interpreted as python code.
