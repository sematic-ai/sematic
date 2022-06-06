#!/bin/bash -x

pip install virtualenv

VENV_NAME=$RANDOM

virtualenv $VENV_NAME

source ./$VENV_NAME/bin/activate

pip install sematic/sematic-0.0.1-py3-none-any.whl

deactivate

rm -rf $VENV_NAME
