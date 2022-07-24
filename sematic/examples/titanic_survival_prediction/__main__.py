# Titianic survival prediction example
from sematic.examples.titanic_survival_prediction.pipeline import pipeline


def main():
    """
    Entry point for examples/titanic_survival_prediction

    Run with

    ```shell
    $ sematic run examples/titanic_survival_prediction
    ```
    """

    pipeline().set(
        name="Titanic survival prediction",
        tags=["Beginner", "EDA", "Classification", "Structured Data"],
    ).resolve()


if __name__ == "__main__":
    main()
