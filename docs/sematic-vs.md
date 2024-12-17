There are many fantastic tools out there to build production-grade Machine
Learning and Data Science pipelines.

## So why Sematic?

We believe our experience at leading tech companies has taught us
a number of important base principles:

### Abstract away infrastructure

Machine Learning (ML) and Data Science (DS) developers are **not** software
engineers, and vice-versa.

While software engineers love nerding out on scalable infrastructure and
beautiful abstractions, ML/DS developers care about a different set of semantics:
models, metrics, plots, distributions, etc.

Therefore, tools built for them should focus on those and abstract away the
rest.

### Lowest barrier to entry

In 2025, with all the great technology there is out there, it is entirely
possible to provide an amazing turn-key onboarding experience with a very low
barrier to entry for all sets of skills, from beginner padawan to advanced
ninja.

Sematic is committed to having you run your first pipelines in a matter of
hours.

### The opinionated/flexibility tradeoff

In our past jobs, we have tried many different tools to achieve similar result:
automating long end-to-end pipelines.

We have found that some of them are so flexible and generic that additional
layers need to be built on top, which is out of reach for users without a
dedicated platform team.

On the other hand, some tools are so opinionated that doing anything outside
the bounds prescribed by the framework is simply not possible.

At Sematic, we strive to hit the right balance of constraints to make work fast
and effortless, and flexibility to not hinder our users' creativity.

## Sematic vs. ...

{% hint style="warning" %}

In this section we try to discuss Sematic's differentiators in the most candid
and transparent way possible.

{% endhint %}

### ... Airflow

Airflow is probably the most popular and widespread way to build end-to-end
pipelines, since it was one of the first to provide such abilities.

Sematic differs from Airflow in the following ways:

* **Iterative development** – change code, run in the cloud, visualize, repeat. In Airflow, you can either run a pipeline on a local Airflow instance, or if you want to run it in the cloud, you must merge your code and deploy it to the cloud instance which adds many steps to your iteration workflow. In Sematic, you can execute your pipeline entirely locally while you develop: you can even run it without running a local server if you want to! And when you are ready for cloud execution, a single command is all you need to package, submit, and execute.

* **Semantic UI** – Sematic brings visualizations for your functions inputs and outputs straight to the forefront. No need to take care of persisting things elsewhere or fetching them into a local notebook.

* **Dynamic graph** – Sematic lets up loop over configurations, run different branches of your pipelines depending on the outcome of upstream steps, and even do hyperparameter tuning.

* **Dead simple I/O between steps** – Sematic makes I/O between steps in your pipelines as simple as passing an output of one
python function as the input of another. Airflow provides APIs which can pass data between tasks, but involves
some boilerplate around explicitly pushing/pulling data around, and coupling producers and consumers via named data keys.

### ... Kubeflow Pipelines

* **Low Barrier to entry** – Using KFP requires quite a bit of knowledge about
  Kubernetes, Docker images, Argo, etc. These things take a lot of time to
  master. Sematic tries to provide working solutions out-of-the-box so that you
  can focus on your expertise instead of infrastructure.

* **Dynamic graph** – In KFP, DAGs are fixed ahead of time. While it does provide
some mechanisms to modify pipeline behavior mid-execution, you are limited by the provided
control flow statements. Sematic lets you use standard python control flow to loop over
configurations, run different branches of your pipelines depending on the outcome of upstream
steps, and even do hyperparameter tuning.

* **Lineage tracking** – KFP has some basic tracking of artifacts flowing between your steps, but is limited in the
type of data that can be tracked in this way. If you want to have tracking for high-level, typed objects like "models"
instead of just paths to blobs, you need to implement that yourself on top of it. In Sematic, lineage tracking of richly
typed artifacts is a first-class citizen. All inputs and outputs of all Sematic Functions are tracked and versioned.

* **Semantic UI** – The KFP UI offers barebones tools to monitor and inspect runs, but no rich visualization or advanced features.

### ... MLFlow Pipelines

* **Flexibility** - To use MLFlow Pipelines, you are limited to a pre-defined set of pipeline
templates. Sematic lets you build any pipeline structure you like.

* **Pythonic SDK** - Using MLFlow requires using a yaml-based configuration combined with
Jinja templating to enable hierarchical config specifications. Sematic lets you stick with
simple python for constructing your pipeline and feeding in configurations and other inputs.

* **Powerful compute access** - MLFlow pipelines run natively on Databricks VMs, or
you can execute them on your own VMs if you manually integrate it with your own job
execution solution. Sematic lets each step in your pipeline run with the computing
resources that are appropriate for it.

### ... Dagster
* **Use case** – Dagster is designed to define data workflows, or lightweight
  Data Science and Machine Learning workflows. Sematic is designed to Machine
  Learning pipelines of arbitrary complexity using heterogeneous compute. For
  example, Sematic lets you chain data processing jobs (e.g. Spark, Beam) with
  long-running GPU training jobs (e.g. Tensorflow, PyTorch), or steps using
  platform custom-built by your company.

* **Semantic UI** – Sematic has rich visualizations for the inputs and outputs at all levels
of your pipelines. Instead of specifying configurations with yaml in your browser, you can
fill out web forms that have just the fields expected, with appropriate validation
([this feature coming soon!](https://trello.com/c/rjLo3cuP/21-ui-reruns)). You can also get
automatic links to data in external systems like Snowflake straight from the UI for your executions.

* **Natural control flow** - In Dagster, options for creating dynamic pipelines are
limited and require using custom APIs
dedicated to the purpose. In Sematic, you can define dynamic pipelines as easily as this:

```python
@sematic.func
def my_dynamic_pipeline() -> MyResult:
  partial_result = another_sematic_func()
  return do_a_or_b(partial_result)

@sematic.func
def do_a_or_b(partial_result: MyPartialResult) -> MyResult:
  if partial_result.some_bool:
    return do_a_sematic_func()
  else:
    return do_b_sematic_func()
```

### ... Prefect
* **Use case** – Prefect targets Data Engineers who build data pipelines (e.g.
  ETL), while Sematic targets ML Engineers building ML model training pipelines.
  Arguably these two use cases can overlap at times, but Sematic really focuses
  on ease-of-use and fast iterative development for users with no infrastructure
  skills.

* **Semantic UI** – Sematic has rich visualizations for the inputs and outputs at all levels
of your pipelines. Instead of having to search through logs to find out what was executed or
what the result was, you can see this information right on the page for the execution. You
can also reconfigure directly from the UI and re-execute
([re-run feature coming soon!](https://trello.com/c/rjLo3cuP/21-ui-reruns)).

* **Seamless Packaging** - Instead of having to learn and manage a manifest system unique to
the orchestration product, use the dependency management solution you're already using to let
Sematic build a docker image that can be used to execute your code in the cloud.

### ... Comet ML

Comet ML specializes in experiment tracking. If this is a particular concern of
yours, you can definitely use Comet ML with Sematic. They are complementary
tools.

### ... Weights & Biases

Weights & Biases excels at experiment tracking and visualization. You can
absolutely use W&B together with Sematic, they are complementary tools.

### ... HuggingFace

HuggingFace provides a large collection of pre-trained models and datasets. You
can absolutely use HuggingFace with Sematic.
