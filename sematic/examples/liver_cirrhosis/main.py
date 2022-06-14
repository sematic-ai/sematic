# Standard library
import os

# Liver cirrhosis
from sematic.examples.liver_cirrhosis.pipeline import pipeline


if __name__ == "__main__":
    csv_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "data", "cirrhosis.csv"
    )

    pipeline(csv_path).set(
        name="Liver disease prediction",
        tags=["example", "seaborn", "matplotlib", "pandas"],
    ).resolve()
