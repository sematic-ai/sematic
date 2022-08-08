# Types

Sematic comes with a number of types for greater convenience.

## `Link` type

If you need to output a URL in one of your Sematic functions and you would like
this URL to be clickable in the UI. Use the `Link` type as such:

```python
from sematic.types import Link

@sematic.func
def my_function() -> Link:
    return Link(
        label="Sematic documentation",
        url="https://docs.sematic.dev",
    )
```

and the following button will show up in the UI:

![Link view in the UI](https://user-images.githubusercontent.com/429433/183307054-5361cb1d-fba2-4b81-80b4-fc73b817b1d9.png)

Note that you can also return an instance of `Link` as part of a dataclass,
list, tuple, or dictionary as well.