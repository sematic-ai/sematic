## Sematic decorator

### `@sematic.func`

The Sematic Function decorator.

This identifies the function as a unit of work that Sematic knows about for
tracking and scheduling. The function's execution details will be exposed
in the Sematic UI.

#### Parameters

- `func`: Optional[Callable]
    
    The `Callable` to instrument; usually the decorated function.

- `inline`: bool
    
    When using the `CloudResolver`, whether the instrumented function
    should be executed inside the same process and worker that is executing
    the `Resolver` itself.

    Defaults to `True`, as most pipeline functions are expected to be
    lightweight. Explicitly set this to `False` in order to distribute its
    execution to a worker and parallelize its execution.

- `cache`: bool

    Whether to cache the function's output value under the `cache_namespace`
    configured in the `Resolver`. Defaults to `False`.

    Do not activate this on a non-deterministic function!

- `resource_requirements`: Optional[ResourceRequirements]

    When using the `CloudResolver`, specifies what special execution
    resources the function requires. Defaults to `None`.

- `retry`: Optional[RetrySettings]
    
    Specifies in case of which Exceptions the function's execution should
    be retried, and how many times. Defaults to `None`.

#### Returns

Union[Calculator, Callable]

An internal instrumentation wrapper over the decorated function.

## Resolvers

### `Resolver`

Abstract base class for all resolvers. Defines the `Resolver` interfaces.

#### `Resolver.resolve`

Abstract method. Entry-point for the resolution algorithm.

##### Parameters

- `future`: AbstractFuture
    
    Root future of the graph to resolve.

##### Returns

Any

output of the pipeline.

### `LocalResolver`

A resolver to resolver a graph in-memory.

Each Future's resolution is tracked in the DB as a run. Each individual function's
input arguments and output value are tracked as artifacts.

#### Parameters

- `cache_namespace`: CacheNamespace

    A string or a `Callable` which takes a root `Future` and returns a string, which
    will be used as the cache key namespace in which the executed funcs' outputs will
    be cached, as long as they also have the `cache` flag activated. Defaults to
    `None`.

    The `Callable` option takes as input the `Resolution` root `Future`. All the other
    required variables must be enclosed in the `Callables`' context. The `Callable`
    must have a small memory footprint and must return immediately!

- `rerun_from`: Optional[str]
    
    When `None`, the pipeline is resolved from scratch, as normally. When not `None`,
    must be the id of a `Run` from a previous resolution. Instead of running from
    scratch, parts of that previous resolution is cloned up until and including the
    specified `Run`, and only nested and downstream `Future`s are executed. This is
    meant to be used for retries or for hotfixes, without needing to re-run the
    entire pipeline again.

### `CloudResolver`

Resolves a pipeline on a Kubernetes cluster.

#### Parameters

- `cache_namespace`: CacheNamespace

    A string or a `Callable` which takes a root `Future` and returns a string, which
    will be used as the cache key namespace in which the executed funcs' outputs will
    be cached, as long as they also have the `cache` flag activated. Defaults to
    `None`.

    The `Callable` option takes as input the `Resolution` root `Future`. All the other
    required variables must be enclosed in the `Callables`' context. The `Callable`
    must have a small memory footprint and must return immediately!

- `max_parallelism`: Optional[int]

    The maximum number of non-inlined runs that this resolver will allow to be in the
    `SCHEDULED` state at any one time. Must be a positive integer, or `None` for
    unlimited runs. Defaults to `None`.

    This is intended as a simple mechanism to limit the amount of computing resources
    consumed by one pipeline execution for pipelines with a high degree of
    parallelism. Note that if other resolvers are active, runs from them will not be
    considered in this parallelism limit. Note also that runs that are in the RAN
    state do not contribute to the limit, since they do not consume computing
    resources.

- `rerun_from`: Optional[str]

    When `None`, the pipeline is resolved from scratch, as normally. When not `None`,
    must be the id of a `Run` from a previous resolution. Instead of running from
    scratch, parts of that previous resolution is cloned up until and including the
    specified `Run`, and only nested and downstream `Future`s are executed. This is
    meant to be used for retries or for hotfixes, without needing to re-run the
    entire pipeline again.

### `SilentResolver`

A resolver to resolver a DAG in memory, without tracking to the DB.

## Resource requirements

### `ResourceRequirements`

#### Parameters

- `kubernetes`: KubernetesResourceRequirements

    Kubernetes resource requirements.

### `KubernetesResourceRequirements`

Information on the Kubernetes resources required.

#### Parameters

- `node_selector`: Dict[str, str]

    The kind of Kubernetes node that the job must run on. More details can be
    found here:
    https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/ The
    value of this field will be used as the nodeSelector described there.

- `requests`: Dict[str, str]

    Requests for resources on a kubernetes pod. More details can be found here:
    https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
    The values used here will apply to both the "requests" and the "limits" of
    the job.

- `secret_mounts`: KubernetesSecretMount

    Requests to take the contents of Kubernetes secrets and expose them as
    environment variables or files on disk when running in the cloud.

- `tolerations`: List[KubernetesToleration]

    If your Kubernetes configuration uses node taints to control which workloads
    get scheduled on which nodes, this enables control over how your workload
    interacts with these node taints. More information can be found here:
    https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

- `mount_expanded_shared_memory`: bool

    By default, Docker uses a 64MB /dev/shm partition. If this flag is set, a
    memory-backed tmpfs that expands up to half of the available memory file is used
    instead. Defaults to False. If that file is expanded to more than that limit
    (through external action), then the pod will be terminated.

### `KubernetesSecretMount`

Information about how to expose Kubernetes secrets when running a Sematic func.

This can be used to mount credentials that the func may need to execute. To use it
in this manner:

1. Create a Kubernetes secret containing the credentials you need. The secret MUST be
    named "sematic-func-secrets" Instructions for this can be found here:
    https://kubernetes.io/docs/concepts/configuration/secret/
    In the "data" field of the secret, you should have key value pairs for every
    secret value you wish to expose for Sematic functions. For example, you might
    have the key `my-api-key` and the value `mYSu93Rs3cretKey`

2. For the Sematic func that requires access to the secret, list it either as an
    environment secret (the secret's value will be stored in an environment variable)
    or as a file secret (the secret's value will be stored in a file).

Before using Kubernetes secrets to give this kind of credential access, be aware that
using them will allow anybody who can execute Sematic funcs in your cluster access to
the secrets.

#### Parameters

- `environment_secrets`: Dict[str, str]

    A dict whose keys are the same as the subset of keys from the
    "sematic-func-secret" that you want mounted for the func, and whose values are
    the name of the environment variable where it should be exposed

- `file_secrets`: Dict[str, str]

    A dict whose keys are the same as the subset of keys from the
    "sematic-func-secret" that you want mounted for the func, and whose values are
    the path to the file within the container where the secret should be exposed.
    These file paths should be RELATIVE paths, they will be taken as relative to
    file_secret_root_path.

- `file_secret_root_path`: str

    File secrets must all be stored in the same directory. This gives the directory
    where they will be stored. The directory must be a new directory, or the contents
    of the existing directory will be overwritten.

### `KubernetesToleration`

Toleration for a node taint, enabling the pod for the function to run on the node

See Kubernetes documentation for more:
https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

#### Parameters

- `key`: Optional[str]

    The key for the node taint intended to be tolerated. If empty, means
    to match all keys AND all values

- `operator`: KubernetesTolerationOperator

    The way to compare the key/value pair to the node taint's key/value pair
    to see if the toleration applies

- `effect`: KubernetesTolerationEffect

    The effect of the node taint the toleration is intended to tolerate.
    Leaving it empty means to tolerate all effects.

- `value`: Optional[str]

    If the operator is Equals, this value will be compared to the value
    on the node taint to see if this toleration applies.

- `toleration_seconds`: Optional[int]

    Only specified when effect is NoExecute (otherwise is an error). It
    specifies the amount of time the pod can continue executing on a node
    with a NoExecute taint

### `KubernetesTolerationEffect`

The effect that the toleration is meant to tolerate

See Kubernetes documentation for more:
https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

#### Values

- `KubernetesTolerationEffect.NoSchedule`
    The toleration indicates that the pod can run on the node even
    if it has specified a NoSchedule taint, assuming the rest of
    the toleration matches the taint.

- `KubernetesTolerationEffect.PreferNoSchedule`

    The toleration indicates that the pod can run on the node even
    if it has specified a PreferNoSchedule taint, assuming the rest
    of the toleration matches the taint.

- `KubernetesTolerationEffect.NoExecute`

    The pod will not be evicted from the node even if the node has
    specified a NoExecute taint, assuming the rest of the toleration
    matches the taint.

- `KubernetesTolerationEffect.All`

    The pod will not be evicted from the node even if the node has
    any kind of taint, assuming the rest of the toleration
    matches the taint.

### `KubernetesTolerationOperator`

The way that a toleration should be checked to see if it applies.

See Kubernetes documentation for more:
https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

#### Values

- `KubernetesTolerationOperator.Equal`

    value must be specified, and must be equal for the toleration and the taint
    for the toleration to be considered to apply. In addition to this condition,
    the "effect" must be equal for the toleration and the taint for the toleration
    to be considered to apply.

- `KubernetesTolerationOperator.Exists`

    value is not required. If a taint with the given key exists on the node,
    the toleration is considered to apply. In addition to this condition,
    the "effect" must be equal for the toleration and the taint for the toleration
    to be considered to apply.

## Fault tolerance

### `RetrySettings`

Configuration object to pass to `@sematic.func` to activate retries.

#### Parameters

- `exceptions`: Tuple[Type[Exception]]

    A tuple of exception types to retry for.

- `retries`: int

    How may times to retry.

## Context

### `SematicContext`

Contextual information about the execution of the current Sematic function

#### Attributes

- `run_id`: str

    The id of the future for the current execution. For cloud executions, this
    is equivalent to the id for the existing run.

- `root_id`: str

    The id of the root future for a resolution. For cloud executions, this is
    equivalent to the id for the root run.

### `context`

Get the current run context, including the active run id and root run id.

This can be used if you wish to track information about a Sematic execution
in an external system, and store it by an id that can link you back to the
Sematic run. It should not be used to interact with the Sematic API directly.

#### Returns

`SematicContext`

The active context, if a Sematic function is currently executing. Otherwise
it will raise an error.

#### Raises

- `NotInSematicFuncError`

    If this function is called outside the execution of a Sematic function.

## Types

### `Link`

Link lets users return a URL from a Sematic function which will render as a
button in the UI.

#### Parameters

- `label`: str

    The label of the button that will be displayed in the UI

- `url`: str

    The URL to link to

#### Raises

- `ValueError`

    In case of missing URL scheme and netloc as extracted by `urllib.parse.urlparse`.


### `SnowflakeTable`

A class to easily access Snowflake tables.

The following user settings need to be set:

```shell
$ sematic settings set SNOWFLAKE_USER <george>
$ sematic settings set SNOWFLAKE_PASSWORD <across-the-universe>
$ sematic settings set SNOWFLAKE_ACCOUNT <the-beatles>
```

#### Parameters

- `database`: str

    Name of Snowflake database

- `table`: str

    Name of Snowflake table

#### `Snowflake.to_df`

Output content of the table to a `pandas.DataFrame`.

##### Parameters

- `limit`: Optional[int]
    
    Maximum number of rows to return. Defaults to -1, i.e. all.
