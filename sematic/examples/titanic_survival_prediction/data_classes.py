# Standard library
from dataclasses import dataclass

# Third-party
import pandas as pd
import matplotlib.figure


@dataclass
class EvaluationOutput:
    classification_report: pd.DataFrame
    confusion_matrix: pd.DataFrame


@dataclass
class EDAPlots:
    survival_gender_figure: matplotlib.figure.Figure
    survival_class_figure: matplotlib.figure.Figure


@dataclass
class PipelineOutput:
    evaluation_results: EvaluationOutput
    eda_plots: EDAPlots
