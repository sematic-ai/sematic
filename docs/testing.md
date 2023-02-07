# Testing Sematic Pipelines

As a tool for creating
[Continuous Learning](https://medium.com/sematic-blog/continuous-learning-for-safer-and-better-ml-models-42e51851b4bd)
pipelines, Sematic fully appreciates the value of tests. Regardless of whether
your pipeline is handling updates to a production machine learning model,
manipulating some internal data, or doing regression testing itself, it's
important to make sure the pipeline itself is healthy. You don't want to
have your pipeline execute for hours or days, and then have it fail near
the end for a simple error!

Sematic will perform some up-front checks, like performing some early
[type checking](https://docs.sematic.dev/type-support/type-support)
between the inputs and outputs of the funcs in your pipeline.
However, there's nothing that replaces the value of a good, fast unit test.
To aid in the creation of pipeline unit tests, Sematic provides
`sematic.testing.mock_sematic_funcs`. It can be used as follows:

```python
import pytest
import sematic
from sematic.resolvers.silent_resolver import SilentResolver
from sematic.testing import mock_sematic_funcs


@sematic.func
def pipeline() -> int:
    return do_sum([remote_only_func(1), remote_only_func(2), identity_func(3)])


@sematic.func
def do_sum(ints: List[int]) -> int:
    return sum(ints)


@sematic.func
def remote_only_func(x: int) -> int:
    raise ValueError("Oh no! This function doesn't work when you're testing")


@sematic.func
def identity_func(x: int) -> int:
    return x


def test_mock_sematic_funcs():
    with mock_sematic_funcs([remote_only_func]) as mock_funcs:

        # You can access handles to the mocks using the context object
        # and the sematic funcs as keys. The .mock field is a
        # unittest.mock.MagicMock that represents a mock for the
        # underlying code before it had @sematic.func applied
        mock_funcs[remote_only_func].mock.return_value = 1

        # The SilentResolver is great for tests: it executes your pipeline
        # locally and without making any API calls
        result = pipeline().resolve(SilentResolver())

        # sum([1, 1, 3])
        assert result == 5

    with mock_sematic_funcs([remote_only_func, identity_func]) as mock_funcs:
        mock_funcs[remote_only_func].mock.return_value = 1

        # you can access the original function, as it was before
        # @sematic.func was applied. This can be handy if you only
        # want to verify that the original was called, but still
        # want it to behave as it always did
        mock_funcs[identity_func].mock.side_effect = mock_funcs[identity_func].original
        result = pipeline().resolve(SilentResolver())

        # sum([1, 1, 3])
        assert result == 5
        
        mock_funcs[identity_func].mock.assert_called()
    
    # Even when you've mocked a Sematic func, type checking will still
    # occur to make sure the connections between the inputs and outputs
    # in the pipeline are all correct. During execution, calling the
    # funcs will always return unresolved futures at first as well, just
    # as they do in a real (unmocked) execution. This helps ensure that
    # your "future" logic is all correct. These checks are the primary
    # advantage of mocking with Sematic's mock_sematic_funcs instead of
    # unittest.mock mocking mechanisms. 
    with pytest.raises(
        TypeError,
        match=r"for 'sematic.testing.tests.test_mock_funcs.remote_only_func'.*",
    ):
        with mock_sematic_funcs([remote_only_func]) as mock_funcs:
            mock_funcs[remote_only_func].mock.return_value = "this is the wrong type!"
            pipeline().resolve(SilentResolver())
    
    # The mocking only lasts within the `with` context
    assert identity_func(16).resolve(SilentResolver()) == 16
```

Note that this is able to test the connections between your pipeline
using familiar python mechanisms. This is one more advantage of using Sematic
over traditional CI tools or container-oriented tooling for ML pipelines.