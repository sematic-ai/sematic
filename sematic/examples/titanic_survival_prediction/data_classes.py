# Standard library
from dataclasses import dataclass

# Third-party
import pandas as pd

@dataclass
class EvaluationOutput:
    confusion_matrix: pd.DataFrame
    classification_report: pd.DataFrame

@dataclass
class TrainTestData:
    train_data: pd.DataFrame
    test_data: pd.DataFrame

@dataclass
class TrainTestSplit:
    train_features: pd.DataFrame
    train_labels: pd.DataFrame
    test_features: pd.DataFrame
    test_labels: pd.DataFrame
