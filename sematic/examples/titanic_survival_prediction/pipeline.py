# Standard library
from typing import List, Tuple, Union

# Third-party
import matplotlib.figure

# TODO move data class below sematic
# Sematic
import sematic

# Data class
from sematic.examples.titanic_survival_prediction.data_classes import EvaluationOutput

# Titianic survival prediction example
from sematic.examples.titanic_survival_prediction.data_preprocessing import (
    load_data,
    feature_engineering,
    split_data
)
from sematic.examples.titanic_survival_prediction.plots import make_eda_plots
from sematic.examples.titanic_survival_prediction.model import init_model
from sematic.examples.titanic_survival_prediction.train import train_model
from sematic.examples.titanic_survival_prediction.test import eval_model

@sematic.func
def pipeline() -> Tuple[EvaluationOutput, matplotlib.figure.Figure]:
    """
    Titanic survial prediction as [implemented
    here](https://www.jcchouinard.com/classification-machine-learning-project-in-scikit-learn/)
    """
    feature_label_dataframes = load_data().set(
        name="Load Data", tags=["data loading"]
    )

    eda_plots = make_eda_plots(feature_label_dataframes).set(
        name="EDA Analysis", tags=["eda analysis"]
    )

    feature_label_dataframes = feature_engineering(feature_label_dataframes).set(
        name="Feature Engineering", tags=["feature engineering"]
    )

    train_test_split_dataframes = split_data(feature_label_dataframes).set(
        name="Split Data", tags=["data splitting"]
    )

    model = init_model().set(
        name="Initialise Model", tags=["model initialising"]
    )

    trained_model = train_model(model, train_test_split_dataframes).set(
        name="Train Model", tags=["model training"]
    )

    evaluation_results = eval_model(trained_model, train_test_split_dataframes).set(
        name="Evaluate Model", tags=["model evaluation"]
    )

    return evaluation_results, eda_plots
