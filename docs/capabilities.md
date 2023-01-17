Sematic is designed to support arbitrarily complex pipelines of Python-defined
business logic running on heterogeneous compute. Pipeline steps can notably include:

* **Data processing** – Apache Spark jobs, Google Dataflow jobs, or other map/reduce jobs
* **Model training and evaluation** – PyTorch, Tensorflow, XgBoost, Scikit Learn, etc.
* **Metrics extraction** – extract aggegate metrics from model inferences or feature datasets
* **Hyperparameter tuning** – iterate on configurations and trigger training jobs
* **Post to third-party APIs** – post labeling requests, JIRA tickets, Slack messages, etc.
* **Arbitrary Python logic** – really anything that can be implemented in Python

## Iterative development

Sematic lets you iterate on, prototype, and debug your pipelines on your local
development machine, then submit them to execute in a Kubernetes cluster in your
cloud environment and leverage cloud resources such as GPUs and large memory
instances.

Sematic packages your local code and dependencies at runtime so that you can
make local code changes and view their impact at scale easily.

## Automated end-to-end ML training pipelines

Sematic is meant to support end-to-end ML training pipelines. End-to-end means
the ability to produce a final model artifact from raw, labelled data sitting in
a data warehouse.

The steps in your pipelines could be:

* **Data mining** – select the data on which you want to train, remove outliers,
  apply selection criteria. This could be implemented e.g. as a Python function
  querying a BigQuery table and storing the output in another one.
* **Data processing** – process the selected data into a feature dataset ready
  for model training. For example, use Apache Spark to efficiently rotate
  images, normalize distributions, one-hot-encode classifications, prepare
  tensors for training, etc.
* **Model training** – consume the prepared dataset into a PyTorch or Tensorflow GPU job
  to produce a series of checkpoints and trained models.
* **Model evaluation** – use the trained model to generate inferences on a test
  dataset to evaluate performance of the model.
* **Metrics extraction** – extract aggregate safety and performance metrics of your
  model and output plots and graphs for human review.
* **Model deployement** – deploy the trained model behind a endpoint to expose it to
  your production system.

Once these steps are automated in an end-to-end pipeline, they can be scheduled
or rerun on new data with very little engineering effort.

## Data pipelines

With Sematic, you can orchestrate arbitrary data processing steps.

For example, you can chain SQL queries with Spark jobs, with Pandas Dataframe
processing steps, and write all intermediate steps to your data warehouse, or
cloud storage bucket.

## Regression testing

You can use Sematic as part of your CI pipelines to trigger regression testing jobs.

Every time you make changes to your data processing or training code, you want
to trigger a pipeline to train your model and generate inferences on a golden
dataset and ensure no regressions were introduced.

This can be achieved by launching a Sematic pipeline from a CI build tool.

## Data Science pipelines

Even if you're not training models, you can use Sematic to implement Data
Science pipelines that run statistical modeling and extract plots and metrics
from your production data.