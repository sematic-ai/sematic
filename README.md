![Sematic logo](https://github.com/sematic-ai/sematic/raw/main/docs/images/Logo_README.png)

---------------

<p align="center">Prototype to production ML in days not weeks</p>

![UI Screenshot](https://github.com/sematic-ai/sematic/raw/main/docs/images/Screenshot_README_1.png)

[![CircleCI](https://img.shields.io/circleci/build/github/sematic-ai/sematic/main?label=CircleCI&style=for-the-badge&token=c8e0115ddccadc17b98ab293b32cad27026efb25)](https://app.circleci.com/pipelines/github/sematic-ai/sematic?branch=main&filter=all)
![PyPI - License](https://img.shields.io/pypi/l/sematic?style=for-the-badge)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=none)](https://python.org)
![Discord](https://img.shields.io/discord/983789877927747714?label=DISCORD&style=for-the-badge)
[![Made By Sematic](https://img.shields.io/badge/Made_by-Sematic_🦊-E19632?style=for-the-badge&logo=none)](https://sematic.ai)

## Welcome to Sematic.

Sematic is an open-source development toolkit to help Data Scientists and Machine
Learning (ML) Engineers prototype and productionize ML pipelines in days not
weeks.

Find our docs at [docs.sematic.ai](https://docs.sematic.ai).



## Installation

Instal Sematic with

```shell
$ pip install sematic
```

## Usage

Start the app with

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
$ sematic run my_new_project.main
```


See our docs at [docs.sematic.ai](https://docs.sematic.ai), and join us on [Discord](https://discord.gg/PFCpatvy).

## Contribute

See our Contributor guide at [docs.sematic.ai](https://docs.sematic.ai).
