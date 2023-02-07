#!/bin/bash -x

pip install virtualenv

if [ -z "$CI_VENV_NAME" ]
then
    VENV_NAME=$RANDOM
else
    VENV_NAME=$CI_VENV_NAME
    cd ~/project
fi

virtualenv $VENV_NAME

pwd

source ./$VENV_NAME/bin/activate

pip install bazel-bin/sematic/sematic-*.whl

deactivate

# Only purge the VENV in non-CI environments
if [ -z "$CI_VENV_NAME" ]
then
    rm -rf $VENV_NAME
fi

