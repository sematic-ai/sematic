# Standard Library
from dataclasses import dataclass

# Third-party
import matplotlib.figure
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

# Sematic
import sematic
from sematic.examples.liver_cirrhosis.data_processing import (
    fill_na,
    load_data,
    pre_process,
)
from sematic.examples.liver_cirrhosis.plots import (
    plot_disease_across_features,
    plot_feature_distributions,
    plot_negative_correlations,
    plot_positive_correlations,
    plot_stage_counts,
)

# Liver cirrhosis
from sematic.examples.liver_cirrhosis.train import TrainingOutput, train_model


@dataclass
class PipelineOutput:
    stage_counts: matplotlib.figure.Figure
    disease_across_features: matplotlib.figure.Figure
    feature_distributions: matplotlib.figure.Figure
    positive_correlations: matplotlib.figure.Figure
    negative_correlations: matplotlib.figure.Figure
    logistic_regression_output: TrainingOutput
    xgboost_output: TrainingOutput


@sematic.func
def make_output(
    stage_counts: matplotlib.figure.Figure,
    disease_across_features: matplotlib.figure.Figure,
    feature_distributions: matplotlib.figure.Figure,
    positive_correlations: matplotlib.figure.Figure,
    negative_correlations: matplotlib.figure.Figure,
    logistic_regression_output: TrainingOutput,
    xgboost_output: TrainingOutput,
) -> PipelineOutput:
    return PipelineOutput(
        stage_counts=stage_counts,
        disease_across_features=disease_across_features,
        feature_distributions=feature_distributions,
        positive_correlations=positive_correlations,
        negative_correlations=negative_correlations,
        logistic_regression_output=logistic_regression_output,
        xgboost_output=xgboost_output,
    )


@sematic.func
def pipeline(csv_path: str) -> PipelineOutput:
    """
    Liver disease prediction model as [implemented on
    Kaggle](https://www.kaggle.com/code/arjunbhaybhang/liver-cirrhosis-prediction-with-xgboost-eda/)

    """
    df = load_data(csv_path)
    df = fill_na(df)
    stage_counts = plot_stage_counts(df)
    disease_across_features = plot_disease_across_features(df)
    feature_distributions = plot_feature_distributions(df)
    positive_correlations = plot_positive_correlations(df)
    negative_correlations = plot_negative_correlations(df)

    training_data = pre_process(df)

    log_model = LogisticRegression(max_iter=5000, solver="saga")
    logistic_regression_output = train_model(log_model, training_data).set(
        name="Logistic Regression"
    )

    xgb_model = XGBClassifier(
        learning_rate=0.75, max_depth=3, random_state=1, gamma=0, eval_metric="error"
    )  # tried learning rate values between range [0.01 - 10] & depth [2-8]
    xgb_output = train_model(xgb_model, training_data).set(name="XGBoost")

    return make_output(
        stage_counts=stage_counts,
        disease_across_features=disease_across_features,
        feature_distributions=feature_distributions,
        positive_correlations=positive_correlations,
        negative_correlations=negative_correlations,
        logistic_regression_output=logistic_regression_output,
        xgboost_output=xgb_output,
    )
