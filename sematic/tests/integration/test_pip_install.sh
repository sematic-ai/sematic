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

WHEEL_PATH=$(ls bazel-bin/sematic/sematic-*.whl)

if test -f "$WHEEL_PATH"; then
    echo "Wheel found at $WHEEL_PATH"
else
    echo "Wheel not present at $WHEEL_PATH"
    exit 1
fi

N_MB_SIZE_LIMIT=10
WHEEL_SIZE_MB=$(python3 -c "import os; print(int(os.path.getsize('$WHEEL_PATH') / 2**20))")

if (( WHEEL_SIZE_BYTES > N_BYTE_SIZE_LIMIT )); then
    echo "Error: Wheel bigger than $N_MB_SIZE_LIMIT Mb. Size: $WHEEL_SIZE_MB Mb"
    exit 1
else
    echo "Wheel is $WHEEL_SIZE_MB Mb"
fi

pip install bazel-bin/sematic/sematic-*.whl
python3 -c "import sematic; print(sematic.__version__)" || exit 1

deactivate

# Only purge the VENV in non-CI environments
if [ -z "$CI_VENV_NAME" ]
then
    rm -rf $VENV_NAME
fi

