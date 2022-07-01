There are many fantastic tools out there to build production-grade Machine
Learning and Data Science pipelines.

## So why Sematic?

We believe our experience at the world's number 1 robotaxi company has taught us
a number of important base principles:

### Abstract away infrastructure

Machine Learning (ML) and Data Science (DS) developers are **not** software
enginers, and vice versa.

While software engineers love nerding out on scalable infrastructure and
beautiful abstractions, ML/DS developers care about a different set of semantics:
models, metrics, plots, distributions, etc.

Therefore, tools built for them should focus on those and abstract away the
rest.

### Lowest barrier to entry

In 2022, with all the great technology there is out there, it is entirely
possible to provide an amazing turn-key onboarding experience with a very low
barrier to entry for all sets of skills, from beginner padawan to advanced
ninja.

Sematic is commited to having you run your first pipelines in a matter of
hours.

### The opinionated/flexibility tradeoff

In our past jobs, we have tried many different tools to achieve similar result:
automating long end-to-end pipelines.

We have found that some of them are so flexible and generic that additional
layers need to be built on top, which is out of reach for users without a
dedicated platform team.

On the other hand, some tools are so opinionated that doing anything outside of
the bounds prescribed by the framework is simply not possible.

At Sematic, we strive to hit the right balance of constraints to make work fast
and effortless, and flexibility to not hinder our users' creativity.

## Sematic vs. _____

{% hint style="warning" %}

In this section we try to discuss Sematic's differentiators in the most candid and transparent way possible.

Sematic is a brand new product (Founded May 2022 👶), and is therefore obviously
not as mature, reliable, or stable as some of these long-established products.

But bear with us, we'll catch up fast!

{% endhint %}

### Airflow

Airflow is probably the most popular and widespread way to build end-to-end
pipelines, since it was the first to provide such abilities.

Sematic differs from Airflow in the following ways:

* Iterative development: change code, run in the cloud, visualize, repeat. In Airflow, you can either run a pipeline on a local Airflow instance, or if you want to run it in the cloud, you must merge your code and deploy it to the cloud instance which adds many steps to your iteration workflow.

* Semantic UI: Sematic brings visualizations for your functions inputs and outputs straight to the forefront. No need to take care of persisting things elsewhere or fetching them into a local notebook.

* Dynamic graph:

### Kubeflow Pipelines

* Barrier to entry:

* Dynamic graph:

* Lineage tracking:

* Semantic UI:

### MLFlow

### Dagster

### Comet ML

Experiment tracking, use Comet ML with Sematic

### Weights & Biases

Experiment tracking, visualizations, use W&B with Sematic

### HuggingFace

Pre-trained models, use HF with Sematic

