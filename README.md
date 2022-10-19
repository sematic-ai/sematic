![Sematic logo](https://raw.githubusercontent.com/sematic-ai/sematic/main/docs/images/Logo_README.png)


<p font-size="2em" align="center">Prototype-to-production ML in days not weeks</p>

![UI Screenshot](https://raw.githubusercontent.com/sematic-ai/sematic/main/docs/images/Screenshot_README_1_framed.png)

![PyPI](https://img.shields.io/pypi/v/sematic?style=for-the-badge)
[![CircleCI](https://img.shields.io/circleci/build/github/sematic-ai/sematic/main?label=CircleCI&style=for-the-badge&token=c8e0115ddccadc17b98ab293b32cad27026efb25)](https://app.circleci.com/pipelines/github/sematic-ai/sematic?branch=main&filter=all)
![PyPI - License](https://img.shields.io/pypi/l/sematic?style=for-the-badge)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=none)](https://python.org)
![Discord](https://img.shields.io/discord/983789877927747714?label=DISCORD&style=for-the-badge)
[![Made By Sematic](https://img.shields.io/badge/Made_by-Sematic_🦊-E19632?style=for-the-badge&logo=none)](https://sematic.dev)
![PyPI - Downloads](https://img.shields.io/pypi/dm/sematic?style=for-the-badge)

## Hi 👋

[Sematic](https://sematic.dev) is an open-source development toolkit to help
Data Scientists and Machine Learning (ML) Engineers prototype and productionize
ML pipelines in days not weeks.

Sematic is based on experience building ML infrastructure at leading tech companies.


Find our docs at [docs.sematic.dev](https://docs.sematic.dev), and join us on
[Discord](https://discord.gg/4KZJ6kYVax).

Sematic helps you

* Develop and run ML pipelines using native Python functions, no new DSL to learn
* Monitor, visualize, and track all inputs and outputs of all pipeline steps in a slick UI
* Collaborate with your team to keep the discussion close to the pipeline as opposed to scattered elsewhere
* Execute your pipelines locally or in your cloud
* [soon] Clone/re-run your pipelines with different inputs/configs
* [soon] Schedule your pipelines to keep your models fresh and relevant

Sematic is an alternative to tools such as KubeFlow Pipelines.


## Installation

Install Sematic with

```shell
$ pip install sematic
```

## Usage

Start the app locally with

```shell
$ sematic start
```

Then run an example pipeline with

```shell
$ sematic run examples/mnist/pytorch
```

Create a new boilerplate project

```shell
$ sematic new my_new_project
```

Or from an existing example:

```shell
$ sematic new my_new_project --from examples/mnist/pytorch
```

Then run it with

```shell
$ python3 -m my_new_project
```


See our docs at [docs.sematic.dev](https://docs.sematic.dev), and join us on
[Discord](https://discord.gg/4KZJ6kYVax).

## Contribute

See our Contributor guide at [docs.sematic.dev](https://docs.sematic.dev).

![scarf pixel](https://static.scarf.sh/a.png?x-pxid=80c3593f-25a0-4b06-90a1-0b670a6567d4)
