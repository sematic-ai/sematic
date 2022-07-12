# Standard library
import argparse
import importlib
import logging

# Sematic
import sematic.api_client as api_client
from sematic.future import Future
from sematic.resolvers.cloud_resolver import CloudResolver


def _get_args():
    parser = argparse.ArgumentParser("Sematic cloud worker")
    parser.add_argument("--run_id", type=str, required=True)
    parser.add_argument("--resolve", default=False, action="store_true", required=False)

    args = parser.parse_args()

    return args


logger = logging.Logger("sematic-worker")


def main(run_id: str, resolve: bool):
    runs, artifacts, edges = api_client.get_graph(run_id)

    if len(runs) == 0:
        raise ValueError("No run with id {}".format(run_id))

    run = runs[0]

    if resolve:
        function_path = run.calculator_path
        logger.info("Importing function %s", function_path)

        module_path = ".".join(function_path.split(".")[:-1])
        function_name = function_path.split(".")[-1]

        module = importlib.import_module(module_path)

        func = getattr(module, function_name)

        future: Future = func()
        future.id = run.id

        resolver = CloudResolver(attach=True)
        resolver.set_graph(runs=runs, artifacts=artifacts, edges=edges)

        resolver.resolve(future)


if __name__ == "__main__":
    args = _get_args()

    logger.info("Worker CLI args: run_id=%s", args.run_id)
    logger.info("Worker CLI args:  resolve=%s", args.resolve)
    print(args.run_id, args.resolve)

    main(args.run_id, args.resolve)
