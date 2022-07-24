# Standard library
from typing import List, Union

# Sematic
import sematic

# Data class
from sematic.examples.titanic_survival_prediction.data_classes import (
    EDAPlots,
    EvaluationOutput,
)

# Titianic survival prediction example
from sematic.examples.titanic_survival_prediction.data_preprocessing import (
    load_data,
    feature_engineering,
    split_data,
)
from sematic.examples.titanic_survival_prediction.plots import make_eda_plots
from sematic.examples.titanic_survival_prediction.model import init_model
from sematic.examples.titanic_survival_prediction.train import train_model
from sematic.examples.titanic_survival_prediction.test import eval_model


@sematic.func
def pipeline() -> List[Union[EvaluationOutput, EDAPlots]]:
    """
    Titanic survial prediction as [implemented
    here](https://www.jcchouinard.com/classification-machine-learning-project-in-scikit-learn/)
    """
    df_X, df_y = load_data().set(name="Load Data", tags=["data loading"])

    eda_plots = make_eda_plots(df_X, df_y).set(
        name="EDA Analysis", tags=["eda analysis"]
    )

    df_X = feature_engineering(df_X).set(
        name="Feature Engineering", tags=["feature engineering"]
    )

    X_train, y_train, X_test, y_test = split_data(df_X, df_y).set(
        name="Split Data", tags=["data splitting"]
    )

    model = init_model().set(name="Initialise Model", tags=["model initialising"])

    trained_model = train_model(model, X_train, y_train).set(
        name="Train Model", tags=["model training"]
    )

    evaluation_results = eval_model(trained_model, X_test, y_test).set(
        name="Evaluate Model", tags=["model evaluation"]
    )

    return [evaluation_results, eda_plots]
