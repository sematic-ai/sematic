# Data class
from sematic.examples.titanic_survival_prediction.data_classes import EvaluationOutput, TrainTestSplit

# Sematic
import sematic

# Third-party
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix, classification_report

@sematic.func
def eval_model(model: DecisionTreeClassifier, train_test_split_dataframes: TrainTestSplit) -> EvaluationOutput:
    X_test, y_test = train_test_split_dataframes.test_features, train_test_split_dataframes.test_labels
    y_pred = model.predict(X_test)
    cr = pd.DataFrame(classification_report(y_test, y_pred, output_dict=True)).T
    cm = pd.DataFrame(confusion_matrix(y_test, y_pred))
    return EvaluationOutput(confusion_matrix=cm, classification_report=cr)