Here are high-level concepts on which Sematic is built.

### Sematic Functions

In Sematic, there are no differences between a pipeline step and a pipeline
(sequence of steps). Everything is simple a Python function. Every pipeline step
is simply a Python function decorated with the `@sematic.func` decorator, and
every pipeline is another such function calling other decorated.

The example below showcases how pipeline steps can be nested into arbitrary
combinations to create sub-pipelines and end-to-end pipelines.

```python
@sematic.func
def generate_data(config: DataConfig, dataset: Dataset) -> FeatureDataset:
    ...
    return dataset

@sematic.func
def split_dataset(config: SplitConfig, dataset: FeatureDataset) -> Tuple[FeatureDataset, FeatureDataset]:
    ...
    return train_dataset, eval_dataset

@sematic.finc
def train(config: TrainingConfig, dataset: FeatureDataset) -> Model:
    ...
    return model
  
@sematic.func
def eval_model(config: EvaluationConfig, dataset: FeatureDataset) -> EvaluationMetrics:
    ...
    return eval_metrics

@sematic.func
def train_eval(
    train_config: TrainingConfig,
    eval_config: EvaluationConfig,
    train_dataset: FeatureDataset,
    eval_dataset: FeatureDataset
) -> EvaluationMetrics:
    """Train/eval sub-pipeline."""
    model = train(train_config, train_data)
    eval_metrics = eval_model(eval_config, eval_dataset, model)
    return eval_metrics

@sematic.func
def pipeline(config: PipelineConfig, data: Dataset) -> EvalMetrics:
    """End-to-end pipeline."""
    feature_dataset = generate_data(config.data_config, data)
    train_data, eval_data = split_dataset(config.split_config, feature_dataset)
    eval_metrics = train_eval(config.train_config, config.eval_config, train_data, eval_data)
    return eval_metrics
```

See [Sematic functions](./functions.md) for more details.

### Futures

Futures are the way Sematic builds a pipeline's execution graph as an in-memory
DAG. Essentially, when you call a Sematic Function, its business logic does not
get executed. Instead, a `Future` object is returned and used to create the
graph.

In the above example, inside the `pipeline` Sematic Function, `feature_dataset`
is not the output of `generate_data`, it is a future of `generate_data`. A
future is essentially a tuple of the function itself and its input arguments:

```
>>> generate_data(config.data_config, data)
Future(generate_data, {"config": config.data_config, "dataset": data})
```

A future is actually executed, i.e. "resolved", when all its inputs are ready
(resolved).

Future objects support a sub-set of the native Python operations. See [Future
algebra](./future-algebra.md) for more details.

### Runs

Runs represent the execution of a Sematic Function. Each Sematic Function will
have a corresponding run in the DB in the web dashboard every time it is
executed.

### Artifacts

Artifacts represent all input arguments, and the output value of all Sematic Functions.

In the following example:

```python
@sematic.func
def generate_data(config: DataConfig, dataset: Dataset) -> FeatureDataset:
    ...
    return dataset
```

three artifacts will be recorded: one for `config`, one for `dataset`, and one
for the output valueof the function.

Artifacts are serialized, persisted (on your local machine or on cloud storage
depending on your deployment), tracked in a metadata database, and visualizable
in the web dashboard.

See [Artifacts](./artifacts.md) for more details.

### Resolvers

Resolvers dictate how your pipeline gets "resolved". Resolving a pipeline means
going through its DAG (in-memory graph of `Future` objects), and proceeding to
executing each step as its inputs are available.

Different resolvers offer different resolution strategies:

- **`SilentResolver`** – will resolve a pipeline without persisting anything to
  disk or the database. This is ideal for testing or iterating without poluting
  the database. This also means that pipelines resolved with `SilentResolver`
  are not tracked and therefore not visualizable in the web dashboard.
- **`LocalResolver`** – will resolve a pipeline on the machine where it was
  called (typically you local dev machine). It will persist artifacts and track
  metadata in the database. Runs will be visualizable in the dashboard. No
  parallelization is applied, the graph is topologically sorted. See [Local
  execution](./local-execution.md).
- **`CloudResolver`** – will submit a pipeline to execute on a Kubernetes
  cluster. This can be used to leverage step-dependent cloud resources (e.g.
  GPUs, high-memory VMs, etc.). See [Cloud resolver](./cloud-resolver.md). Note
  that to submit cloud pipelines, you need to [Deploy Sematic](./deploy.md).