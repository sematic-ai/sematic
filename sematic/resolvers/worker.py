# Standard library
import sys
import os

# print(os.environ)
# print(sys.executable)
# os.environ["PYTHONHOME"] = "/".join(os.path.realpath(sys.executable).split("/")[:-2])

import argparse
import datetime
import importlib
import logging
from typing import Any, Dict, List

# Third-party
import cloudpickle

# Sematic
from sematic.abstract_future import FutureState
import sematic.api_client as api_client
from sematic.calculator import Calculator
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import get_artifact_value, make_artifact
from sematic.db.models.run import Run
from sematic.future import Future
from sematic.resolvers.cloud_resolver import (
    CloudResolver,
    make_nested_future_storage_key,
)
import sematic.storage as storage


def _get_args():
    """
    Get worker CLI arguments, passed to image by K8s job.
    """
    parser = argparse.ArgumentParser("Sematic cloud worker")
    parser.add_argument("--run_id", type=str, required=True)
    parser.add_argument("--resolve", default=False, action="store_true", required=False)

    args = parser.parse_args()

    return args


logger = logging.getLogger(__name__)


def _get_input_kwargs(
    run_id: str, artifacts: List[Artifact], edges: List[Edge]
) -> Dict[str, Any]:
    """
    Get input values for run
    """
    artifacts_by_id = {artifact.id: artifact for artifact in artifacts}

    kwargs = {
        edge.destination_name: get_artifact_value(artifacts_by_id[edge.artifact_id])
        for edge in edges
        if edge.destination_run_id == run_id
        and edge.artifact_id is not None
        and edge.destination_name is not None
    }

    return kwargs


def _fail_run(run: Run):
    """
    Mark run as failed.
    """
    run.future_state = FutureState.FAILED
    run.failed_at = datetime.datetime.utcnow()
    api_client.save_graph(run.id, [run], [], [])


def _get_func(run: Run) -> Calculator:
    """
    Get run's function.
    """
    function_path = run.calculator_path
    logger.info("Importing function %s", function_path)

    module_path = ".".join(function_path.split(".")[:-1])
    function_name = function_path.split(".")[-1]

    module = importlib.import_module(module_path)

    return getattr(module, function_name)


def _set_run_output(run: Run, output: Any, type_: Any, edges: List[Edge]):
    """
    Persist run output, whether it is a nested future or a concrete output.
    """
    logger.info("_set_run_output")
    artifacts = []

    if isinstance(output, Future):
        logger.info("output is future")
        pickled_nested_future = cloudpickle.dumps(output)
        storage.set(make_nested_future_storage_key(output.id), pickled_nested_future)
        run.nested_future_id = output.id
        run.future_state = FutureState.RAN
        run.ended_at = datetime.datetime.utcnow()

    else:
        logger.info("output is concrete")
        artifacts.append(make_artifact(output, type_, store=True))

        # Set output artifact on output edges
        for edge in edges:
            if edge.source_run_id == run.id:
                edge.artifact_id = artifacts[0].id

        run.future_state = FutureState.RESOLVED
        run.resolved_at = datetime.datetime.utcnow()

    api_client.save_graph(run.root_id, [run], artifacts, edges)


def main(run_id: str, resolve: bool):
    """
    Main job logic.

    `resolve` set to `True` will execute the driver logic.
    `resolve` set to `False` will execute the worker logic.
    """
    runs, artifacts, edges = api_client.get_graph(run_id)

    if len(runs) == 0:
        raise ValueError("No run with id {}".format(run_id))

    run = runs[0]

    try:
        func = _get_func(run)
        kwargs = _get_input_kwargs(run.id, artifacts, edges)
    except Exception as e:
        _fail_run(run)
        raise e

    if resolve:
        try:
            future: Future = func(**kwargs)
        except Exception as e:
            _fail_run(run)
            api_client.notify_pipeline_update(run.calculator_path)
            raise e

        future.id = run.id

        resolver = CloudResolver(detach=False)
        resolver.set_graph(runs=runs, artifacts=artifacts, edges=edges)

        resolver.resolve(future)
    else:
        try:
            logger.info("Executing %s", func.__name__)
            output = func.func(**kwargs)
            _set_run_output(run, output, func.output_type, edges)

        except Exception as e:
            logger.error("Run failed:")
            logger.error("%s: %s", e.__class__.__name__, e)

            _fail_run(run)

            raise e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    args = _get_args()

    logger.info("Worker CLI args: run_id=%s", args.run_id)
    logger.info("Worker CLI args:  resolve=%s", args.resolve)

    main(args.run_id, args.resolve)
