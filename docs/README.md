# Hi 👋

Welcome to Sematic.

Sematic is an open-source development platform for Machine Learning (ML) and
Data Science (DS). It lets users develop arbitrarily complex end-to-end
pipelines using nothing other than Python, then execute them on a laptop or on
Kubernetes with no code changes.

Sematic comes with the following guarantees:

* **Ease-of-use** – Sematic aims to provide the easiest onboarding, and to get
  you started in a few minutes. No deployment needed, you can get started on
  your local machine.
* **Traceability** – Sematic pipelines are tracked and can be monitored and
  visualized in a modern web dashboard. All artifacts (inputs/outputs of all
  pipeline steps) are persisted and visualizable.
* **Reproducibility** – Pipelines that are executed in the cloud are
  reproducible for guaranteed debuggability.
* **Local-to-cloud parity** – Sematic aims to make it seamless to scale a local
  prototype into a large-scale cloud pipeline. The same code can run on a laptop
  and on a Kubernetes cluster with little to no changes.

Sematic comprises the following components:

* **A lightweight Python SDK** to define dynamic pipelines of arbitrary complexity
* **An execution backend** to orchestrate pipelines locally or in the cloud
* **A CLI** to interact with Sematic
* **A web dashboard** to monitor pipelines and visualize artifacts

Sematic comes with the following features:

- **Lightweight Python SDK** – define arbitrarily complex end-to-end pipelines
- **Pipeline nesting** – arbitrarily nest pipelines into larger pipelines
- **Dynamic graphs** – Python-defined graphs allow for iterations, conditional branching, etc.
- **Lineage tracking** – all inputs and outputs of all steps are persisted and tracked
- **Runtime type-checking** – fail early with run-time type checking
- **Web dashboard** – Monitor, track, and visualize pipelines in a modern web UI
- **Artifact visualization** – visualize all inputs and outputs of all steps in the web dashboard
- **Local execution** – run pipelines on your local machine without any deployment necessary
- **Cloud orchestration** – run pipelines on Kubernetes to access GPUs and other cloud resources
- **Heterogeneous compute resources** – run different steps on different machines (e.g. CPUs, memory, GPU, Spark, etc.)
- **Helm chart deployment** – install Sematic on your Kubernetes cluster
- **Pipeline reruns** – rerun pipelines from the UI from an arbitrary point in the graph
- **Step caching** – cache expensive pipeline steps for faster iteration
- **Step retry** – recover from transient failures with step retries
- **Metadata and collaboration** – Tags, source code visualization, docstrings, notes, etc.
- **Numerous integrations** – See below

Read how to [Get Started](get-started.md) or join our [Discord
Server](https://discord.gg/4KZJ6kYVax).

If you want to dig deeper, check out the [Sematic Concepts](concepts.md), or the
[Sematic Source Code](https://github.com/sematic-ai/sematic).

## Who we are

The [Sematic team](https://sematic.dev/about-sematic) hails from around the world and
has extensive industry experience in software development, cloud infrastructure,
and Machine Learning tooling.

While searching for the Higgs boson at CERN, developing payment infrastructure
for Instacart, or building ML tooling for Cruise, we encountered a wide variety
of systems, practices, and patterns, which inform the design of Sematic every
day.

We are dedicated to bringing the most powerful tools and infrastructure to DS
and ML developers of all skills and background.

## Sematic contributors

We would be thrilled to have you contribute to Sematic. You can contribute in
many ways including the following:

* [List of good first issues](https://github.com/sematic-ai/sematic/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)
* [Contribute examples](https://docs.sematic.ai/contribute/contributor-guide/contribute-example)

Get in touch with us on [Discord](https://discord.gg/4KZJ6kYVax) to get more info on how to contribute.

## License

Sematic is Apache 2.0 licensed.

![scarf pixel](https://static.scarf.sh/a.png?x-pxid=a87446e5-0e13-40cd-af92-7dd8cd99d22d)