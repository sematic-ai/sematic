![Sematic Logo](https://raw.githubusercontent.com/sematic-ai/sematic/main/docs/images/Logo_README.png)

<h2 align="center">The open-source Continuous Machine Learning Platform</h2>

<h3 align="center">Build ML pipelines with only Python, run on your laptop, or in the cloud.</h3>

![PyPI](https://img.shields.io/pypi/v/sematic/0.28.1?style=for-the-badge)
[![CircleCI](https://img.shields.io/circleci/build/github/sematic-ai/sematic/main?label=CircleCI&style=for-the-badge&token=c8e0115ddccadc17b98ab293b32cad27026efb25)](https://app.circleci.com/pipelines/github/sematic-ai/sematic?branch=main&filter=all)
![PyPI - License](https://img.shields.io/pypi/l/sematic?style=for-the-badge)
[![Python 3.8](https://img.shields.io/badge/Python-3.8-blue?style=for-the-badge&logo=none)](https://python.org)
[![Python 3.9](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=none)](https://python.org)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=none)](https://python.org)
![Discord](https://img.shields.io/discord/983789877927747714?label=DISCORD&style=for-the-badge)
[![Made By Sematic](https://img.shields.io/badge/Made_by-Sematic_🦊-E19632?style=for-the-badge&logo=none)](https://sematic.dev)
![PyPI - Downloads](https://img.shields.io/pypi/dm/sematic?style=for-the-badge)

![Sematic Screenshot](https://raw.githubusercontent.com/sematic-ai/sematic/main/docs/images/Screenshot_README_2.png)

[Sematic](https://sematic.dev) is an open-source ML development platform. It
lets ML Engineers and Data Scientists write arbitrarily complex end-to-end
pipelines with simple Python and execute them on their local machine, in a cloud
VM, or on a Kubernetes cluster to leverage cloud resources.

Sematic is based on learnings gathered at top self-driving car companies. It
enables chaining data processing jobs (e.g. Apache Spark) with model training
(e.g. PyTorch, Tensorflow), or any other arbitrary Python business logic into
type-safe, traceable, reproducible end-to-end pipelines that can be monitored
and visualized in a modern web dashboard.

Read our [documentation](https://docs.sematic.dev) and join our [Discord
channel](https://discord.gg/4KZJ6kYVax).

## Why Sematic

- **Easy onboarding** – no deployment or infrastructure needed to get started,
  simply install Sematic locally and start exploring.
- **Local-to-cloud parity** – run the same code on your local laptop and on your
  Kubernetes cluster.
- **End-to-end traceability** – all pipeline artifacts are persisted, tracked,
  and visualizable in a web dashboard.
- **Access heterogeneous compute** – customize required resources for each
  pipeline step to optimize your performance and cloud footprint (CPUs, memory,
  GPUs, Spark cluster, etc.)
- **Reproducibility** – rerun your pipelines from the UI with guaranteed
  reproducibility of results

## Getting Started

To get started locally, simply install Sematic in your Python environment:

```shell
$ pip install sematic
```

Start the local web dashboard:

```shell
$ sematic start
```

Run an example pipeline:

```shell
$ sematic run examples/mnist/pytorch
```

Create a new boilerplate project:

```shell
$ sematic new my_new_project
```

Or from an existing example:

```shell
$ sematic new my_new_project --from examples/mnist/pytorch
```

Then run it with:

```shell
$ python3 -m my_new_project
```

To deploy Sematic to Kubernetes and leverage cloud resources, see our
[documentation](https://docs.sematic.dev).

## Features

- **Lightweight Python SDK** – define arbitrarily complex end-to-end pipelines
- **Pipeline nesting** – arbitrarily nest pipelines into larger pipelines
- **Dynamic graphs** – Python-defined graphs allow for iterations, conditional
  branching, etc.
- **Lineage tracking** – all inputs and outputs of all steps are persisted and
  tracked
- **Runtime type-checking** – fail early with run-time type checking
- **Web dashboard** – Monitor, track, and visualize pipelines in a modern web UI
- **Artifact visualization** – visualize all inputs and outputs of all steps in
  the web dashboard
- **Local execution** – run pipelines on your local machine without any
  deployment necessary
- **Cloud orchestration** – run pipelines on Kubernetes to access GPUs and other
  cloud resources
- **Heterogeneous compute resources** – run different steps on different
  machines (e.g. CPUs, memory, GPU, Spark, etc.)
- **Helm chart deployment** – install Sematic on your Kubernetes cluster
- **Pipeline reruns** – rerun pipelines from the UI from an arbitrary point in
  the graph
- **Step caching** – cache expensive pipeline steps for faster iteration
- **Step retry** – recover from transient failures with step retries
- **Metadata and collaboration** – Tags, source code visualization, docstrings,
  notes, etc.
- **Numerous integrations** – See below

## Integrations

- **Apache Spark** – on-demand in-cluster Spark cluster
- **Ray** – on-demand Ray in-cluster Ray resources
- **Snowflake** – easily query your data warehouse (other warehouses supported
  too)
- **Plotly, Matplotlib** – visualize plot artifacts in the web dashboard
- **Pandas** – visualize dataframe artifacts in the dashboard
- **Grafana** – embed Grafana panels in the web dashboard
- **Bazel** – integrate with your Bazel build system
- **Helm chart** – deploy to Kubernetes with our Helm chart
- **Git** – track git information in the web dashboard

## Community and resources

Learn more about Sematic and get in touch with the following resources:

- [Sematic landing page](https://sematic.dev)
- [Documentation](https://docs.sematic.dev)
- [Discord channel](https://discord.gg/4KZJ6kYVax)
- [YouTube channel](https://www.youtube.com/@sematic-ai)
- [Our Blog](https://sematic.dev/blog)

## Contribute!

To contribute to Sematic, check out [open issues tagged "good first
issue"](https://github.com/sematic-ai/sematic/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22),
and get in touch with us on [Discord](https://discord.gg/4KZJ6kYVax).


![scarf pixel](https://static.scarf.sh/a.png?x-pxid=80c3593f-25a0-4b06-90a1-0b670a6567d4)
