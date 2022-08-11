# Third-party
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.tree import DecisionTreeClassifier

# Sematic
import sematic
from sematic.examples.titanic_survival_prediction.data_classes import EvaluationOutput


@sematic.func
def eval_model(
    model: DecisionTreeClassifier, X_test: pd.DataFrame, y_test: pd.DataFrame
) -> EvaluationOutput:
    y_pred = model.predict(X_test)
    cr = pd.DataFrame(classification_report(y_test, y_pred, output_dict=True)).T
    cm = pd.DataFrame(confusion_matrix(y_test, y_pred))
    return EvaluationOutput(classification_report=cr, confusion_matrix=cm)
