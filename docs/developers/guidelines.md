# Developer Guidelines

## Code formatting
Code should be formatted by Black and linted by flake8.

## External modules
When possible, use full path to imported function/class to highlight that the object is imported.

Example:
```python
import abc

class Type(abc.ABC):
    pass

```
instead of
```python
from abc import ABC

class Type(ABC):
    pass
```

## Type hints
Type hints should be expressed using the `typing` library when possible in order to provide maximal compliance with MyPy.

`typing` should be imported as is and used as prefix to all types, in order to differentiate `typing` types from our own types which often have the same name.

Example:
```python
import typing

def func(
    a: typing.Optional[str]
) -> typing.Union[str, float]:
    return "abc"
```