# Standard Library
import argparse
import logging

# Sematic
from sematic import CloudResolver, LocalResolver
from sematic.examples.add.pipeline import pipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Sematic add example")
    parser.add_argument("--cloud", action="store_true", default=False)
    parser.add_argument("--detach", action="store_true", default=False)
    parser.add_argument("--rerun-from", default=None)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    future = pipeline(1, 2, 3).set(
        name="Basic add example pipeline", tags=["example", "basic", "final"]
    )

    resolver = (
        CloudResolver(detach=args.detach, rerun_from=args.rerun_from)
        if args.cloud
        else LocalResolver(rerun_from=args.rerun_from)
    )

    result = future.resolve(resolver)

    logging.info(result)
