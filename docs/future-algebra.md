As described in [Sematic Functions](functions.md), decorating a plain Python
function with `@sematic.func` makes it so calling said function returns a Future
instead of the actual output of the function.

## What is a Future?

A Future is simple class containing the following information:

* The function to execute
* Input values to pass, some of which may be [concrete
  values](./glossary.md#concrete-inputs), some of which may be other Futures.

This is how Sematic constructs the execution graph of your pipeline.

For example, in the following code:

```
>>> @sematic.func
    def foo(a: int) -> int:
        return a

>>> f = foo(123)
```

`f` is not equal to `123` it is equal to

```python
Future(foo, {"a": 123})
```

And the in the following case
```
>>> g = foo(foo(123))
```

`g` is equal to

```python
Future(foo, {"a": Future(foo, {"a": 123})})
```

You get the gist 🙂.

## Supported operations

At this very early phase in Sematic, only basic operations are supported.

### Passing and returning

A Future object can be passed as input value to another Sematic Function, or
returned as output value of a parent Sematic Function.

For example

```python
@sematic.func
def add(a: float, b: float) -> float:
    return a + b

@sematic.func
def pipeline(a: float, b: float) -> float
    sum1 = add(a, b)
    sum2 = add(a, b)
    return add(sum1, sum2)
```

In this example, `sum1` and `sum2` are not actual `float` values, but only
Futures of `float` values. They can be passed to another Sematic Function (e.g.
`add` in this case) or returned as the output value of `pipeline`.

{% hint style="info" %}

This ensure support for basic data flow between pipeline steps and arbitrary
nesting of Sematic Functions.

{% endhint %}

{% hint style="info" %}

Note that the inputs of the outermost Sematic Function (i.e. the one on which
you call `.resolve()`) must all be [concrete](./glossary.md#concrete-inputs).

{% endhint %}


### Passing and returning lists of futures

The following example is supported:

```python

@sematic.func
def add(a: float, b: float) -> float:
    return a + b

@sematic.func
def sum_list(l: List[float]) -> float:
    return sum(l)

@sematic.func
def pipeline(a: float, b: float) -> List[float]:
    list1 = [add(a, b), add(a, b)]
    sum1 = sum(list1)
    return [sum1, add(a, b)]
```

Here Sematic will know how to convert `List[Future[float]]` into
`Future[List[float]]`.

## Currently unsupported behaviors

We are working hard to move these unsupported behaviors to the supported section
above. In the meantime, we offer some workarounds.

{% hint style="info" %}

All these workaround rely on the fact that within a Sematic Function, all input
argument are **always** [concrete](./glossary.md#concrete-inputs).

{% endhint %}

### Containers of futures

Passing and returning lists of future is supported as [mentioned
above](#passing-and-returning-lists-of-futures). However, other container
(tuple, dictionaries, dataclasses) are currently not supported.

Here's an example of how to get around this for dataclasses:

```python
@dataclass
class MyOutput:
    foo: int
    bar: float

@sematic.func
def make_output(foo: int, bar: float) -> MyOutput:
    return MyOutput(foo=foo, bar=bar)

@sematic.func
def pipeline(...) -> MyOutput:
    foo = some_sematic_func()
    bar = another_sematic_func()
    return make_output(foo, bar)
```

### Unpacking and iteration

If your future is a `Future[List[T]]`, you cannot currently unpack it or iterate
on it.

Here's a workaround

```python
@sematic.func
def pipeline() -> T:
    future_of_list = some_sematic_func()

    # Not supported
    for item in future_of_list:
        ...
    
    # Do this instead
    output = iterate_on_list(future_of_list)

# Where
@sematic.func
def iterate_on_list(some_list: List[U]) -> T:
    # Here you are guaranteed that `some_list` is concrete.
    for item in some_list:
        ...
```

### Attribute and item access

At this time if `future` is of type `Future[List[T]]`, you cannot do `future[0]`.

If `future` is of type `Future[Dict[K, V]]`, you cannot do `future["some-key"]`.

If `future` is of type `Future[SomeClass]` where `SomeClass` has an attribute
named `foo`, you cannot do `future.foo`.

Here is a workaround for attribute access:

```python
@sematic.func
def get_attr(obj: SomeClass, name: str) -> T:
    return getattr(obj, name)

@sematic.func
def pipeline() -> T:
    future = some_sematic_func()
    return get_attr(future, "foo")
```

Here is a workaround for item access:

```python
@sematic.func
def get_item(obj: List[T], item: int) -> T:
    return obj[item]
```

Use a similar approach for dictionaries.

### Arithmetic operations

At this time, arithmetic operations are not supported on futures.

If `future` is of type `Future[float]`, you cannot do `future + 1`.

Here is a workaround

```python
@sematic.func
def add(a: float, b: float) -> float:
    return a + b

@sematic.func
def pipeline() -> float:
    float_future = some_sematic_func()
    return add(float_future, 1)
```

### Unreturned futures

If a future is not passed as input to a Sematic Function or returned as output
of a parent future, it will not be resolved.

For example, in the following case:

```python
@sematic.func
def pipeline() -> str:
    future = some_sematic_func()
    return "foo"
```

`some_sematic_func` will never be executed. That is because at the current time,
Sematic builds the execution graph by looking for futures that are returned by,
or passed as input arguments to other Sematic Functions.

Here is a workaround:

```python
@sematic.func
def pipeline() -> Tuple[T, str]:
    future = some_sematic_func()
    return future, "foo"
```

## Unsupported behaviors

The following behaviors will not be supported.

### Variadic arguments

Sematic Functions cannot have variadic arguments.

In Python, variadic arguments are of the form `*args` or `**kwargs`.

This would prevent Sematic from clearly defining and typing input and output artifacts.