# Standard Library
import argparse
import datetime
import logging
import os
import pathlib
import tempfile
from typing import Any, Dict, List, Optional

# Third-party
import cloudpickle

# Sematic
import sematic.api_client as api_client
from sematic.abstract_future import FutureState
from sematic.calculator import Calculator
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.factories import get_artifact_value, make_artifact
from sematic.db.models.run import Run
from sematic.future import Future
from sematic.log_reader import log_prefix
from sematic.resolvers.cloud_resolver import (
    CloudResolver,
    make_nested_future_storage_key,
)
from sematic.resolvers.log_streamer import ingested_logs
from sematic.scheduling.external_job import JobType
from sematic.storage import S3Storage
from sematic.utils.exceptions import format_exception_for_run


def parse_args():
    """
    Get worker CLI arguments, passed to image by K8s job.
    """
    parser = argparse.ArgumentParser("Sematic cloud worker")
    parser.add_argument("--run_id", type=str, required=True)
    parser.add_argument("--resolve", default=False, action="store_true", required=False)
    parser.add_argument("--max-parallelism", type=int, default=None, required=False)
    parser.add_argument("--rerun-from", type=str, default=None, required=False)

    args = parser.parse_args()

    return args


logger = logging.getLogger(__name__)


def _get_input_kwargs(
    run_id: str, artifacts: List[Artifact], edges: List[Edge]
) -> Dict[str, Any]:
    """
    Get input values for run.
    """
    artifacts_by_id = {artifact.id: artifact for artifact in artifacts}

    kwargs = {
        edge.destination_name: get_artifact_value(
            artifacts_by_id[edge.artifact_id], storage=S3Storage()
        )
        for edge in edges
        if edge.destination_run_id == run_id
        and edge.artifact_id is not None
        and edge.destination_name is not None
    }

    return kwargs


def _fail_run(run: Run, e: BaseException) -> None:
    """
    Mark run as failed.
    """
    run.future_state = FutureState.FAILED
    run.failed_at = datetime.datetime.utcnow()

    if run.exception_metadata is None:
        # this means the exception probably happened in the Resolver code
        run.exception_metadata = format_exception_for_run(e)
    else:
        # if the run already has an exception marked on it, then it's the innermost cause
        # of the failure; any other exception generated afterwards is done so while trying
        # to handle the failure
        logger.warning("Got exception while handling run failure", exc_info=e)

    api_client.save_graph(run.id, [run], [], [])


def _set_run_output(run: Run, output: Any, type_: Any, edges: List[Edge]):
    """
    Persist run output, whether it is a nested future or a concrete output.
    """
    artifacts = []
    storage = S3Storage()

    if isinstance(output, Future):
        pickled_nested_future = cloudpickle.dumps(output)
        storage.set(make_nested_future_storage_key(output.id), pickled_nested_future)
        run.nested_future_id = output.id
        run.future_state = FutureState.RAN
        run.ended_at = datetime.datetime.utcnow()

    else:
        artifacts.append(make_artifact(output, type_, storage=storage))

        # Set output artifact on output edges
        for edge in edges:
            if edge.source_run_id == run.id:
                edge.artifact_id = artifacts[0].id

        run.future_state = FutureState.RESOLVED
        run.resolved_at = datetime.datetime.utcnow()

    api_client.save_graph(run.root_id, [run], artifacts, edges)


def main(
    run_id: str,
    resolve: bool,
    max_parallelism: Optional[int] = None,
    rerun_from: Optional[str] = None,
):
    """
    Main job logic.

    `resolve` set to `True` will execute the driver logic.
    `resolve` set to `False` will execute the worker logic.
    """
    if not resolve and rerun_from is not None:
        raise ValueError("Can only have non-None rerun_from in resolve mode")

    runs, artifacts, edges = api_client.get_graph(run_id)

    if len(runs) == 0:
        raise ValueError("No run with id {}".format(run_id))

    run = runs[0]

    try:
        func: Calculator = run.get_func()  # type: ignore
        kwargs = _get_input_kwargs(run.id, artifacts, edges)

        if resolve:
            logger.info("Resolving %s", func.__name__)
            future: Future = func(**kwargs)
            future.id = run.id

            resolver = CloudResolver(
                detach=False,
                max_parallelism=max_parallelism,
                rerun_from=rerun_from,
                _is_running_remotely=True,
            )
            resolver.set_graph(runs=runs, artifacts=artifacts, edges=edges)

            resolver.resolve(future)

        else:
            logger.info("Executing %s", func.__name__)
            output = func.func(**kwargs)
            _set_run_output(run, output, func.output_type, edges)

    except Exception as e:
        logger.error("Run failed:")
        logger.error("%s: %s", e.__class__.__name__, e)

        if resolve:
            # refresh the run from the DB in case it was updated from
            # its worker job
            root_run = api_client.get_run(run_id)
            if not FutureState[root_run.future_state].is_terminal():  # type: ignore
                # Only fail here if the root run hasn't already been
                # moved to a terminal state. It may contain a better
                # exception message. If it completed somehow, then it
                # should be in a valid state that we don't want to disrupt.
                _fail_run(root_run, e)
        else:
            _fail_run(run, e)

        if resolve:
            api_client.notify_pipeline_update(run.calculator_path)

        raise e


def _create_log_file_path(file_name: str) -> str:
    temp_dir = tempfile.gettempdir()
    sematic_temp_logs_dir = pathlib.Path(temp_dir) / pathlib.Path("sematic_logs")
    if not pathlib.Path(sematic_temp_logs_dir).exists():
        os.mkdir(sematic_temp_logs_dir)
    return (pathlib.Path(sematic_temp_logs_dir) / pathlib.Path(file_name)).as_posix()


def wrap_main_with_logging():
    """Wrap the main function with log initialization and ingestion"""
    print("Starting Sematic Worker")
    args = parse_args()
    prefix = log_prefix(args.run_id, JobType.driver if args.resolve else JobType.worker)
    path = _create_log_file_path("worker.log")

    with ingested_logs(path, prefix):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s: %(message)s",
        )
        logger.info("Worker CLI args: run_id=%s", args.run_id)
        logger.info("Worker CLI args: resolve=%s", args.resolve)
        logger.info("Worker CLI args: max-parallelism=%s", args.max_parallelism)
        logger.info("Worker CLI args: rerun_from=%s", args.rerun_from)

        main(
            run_id=args.run_id,
            resolve=args.resolve,
            max_parallelism=args.max_parallelism,
            rerun_from=args.rerun_from,
        )


if __name__ == "__main__":
    # don't put anything here besides wrap_main()! It needs to match
    # bazel/worker.py
    wrap_main_with_logging()
