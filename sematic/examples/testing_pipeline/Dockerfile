FROM sematicai/sematic-worker-base:latest@sha256:bea3926876a3024c33fe08e0a6b2c0377a7eb600d7b3061a3f3f39d711152e3c

# Install pip3
RUN apt-get update -y && apt-get install -y python3-pip
RUN apt-get update -y && apt-get install --reinstall -y python3.9-distutils

COPY sematic/examples/testing_pipeline/requirements.txt requirements.txt
RUN pip3 install --no-cache -r requirements.txt

COPY sematic/examples/testing_pipeline/resources/sematic-0.29.0-py3-none-any.whl sematic-0.29.0-py3-none-any.whl
RUN pip3 install sematic-0.29.0-py3-none-any.whl

COPY sematic/examples/testing_pipeline /usr/local/lib/python3.9/dist-packages/sematic/examples/testing_pipeline
