# Titianic survival prediction example
# Sematic
from sematic import LocalRunner
from sematic.examples.titanic_survival_prediction.pipeline import pipeline


def main():
    """
    Entry point for examples/titanic_survival_prediction

    Run with

    ```shell
    $ sematic run examples/titanic_survival_prediction
    ```
    """

    future = pipeline().set(
        name="Titanic survival prediction",
        tags=["Beginner", "EDA", "Classification", "Structured Data"],
    )
    LocalRunner().run(future)


if __name__ == "__main__":
    main()
