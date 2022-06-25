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

### Containers of futures

### Unpacking and iteration

### Attribute and item access

### Arithmetic operations

### Unreturned futures

