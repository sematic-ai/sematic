<img src="https://github.com/sematic-ai/sematic/raw/main/sematic/ui/public/Logo.png" alt="Sematic" width="400"/>

[![CircleCI](https://circleci.com/gh/sematic-ai/sematic.svg?style=shield&circle-token=c8e0115ddccadc17b98ab293b32cad27026efb25)](<LINK>)

Welcome to Sematic.

Sematic is an open-source development toolkit to help Data Scientists and Machine
Learning (ML) Engineers prototype and productionize ML pipelines in days not
weeks.

Find our docs at [docs.sematic.ai](https://docs.sematic.ai).


![UI Screenshot](https://github.com/sematic-ai/sematic/raw/main/docs/images/Screenshot_README_1.png)

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
