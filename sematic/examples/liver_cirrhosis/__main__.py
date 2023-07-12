# Standard Library
import os

# Sematic
# Liver cirrhosis
from sematic import LocalRunner
from sematic.examples.liver_cirrhosis.pipeline import pipeline


def main():
    """
    Entry point for examples/liver_cirrhosis

    Run with

    ```shell
    $ sematic run examples/liver_cirrhosis
    ```
    """
    csv_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data", "cirrhosis.csv"
    )

    future = pipeline(csv_path).set(
        name="Liver disease prediction",
        tags=["example", "seaborn", "matplotlib", "pandas"],
    )
    LocalRunner().run(future)


if __name__ == "__main__":
    main()
