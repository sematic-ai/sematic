# Sematic
import sematic

# Third-party
import pandas as pd
from sklearn.tree import DecisionTreeClassifier


@sematic.func
def train_model(
    model: DecisionTreeClassifier, X_train: pd.DataFrame, y_train: pd.DataFrame
) -> DecisionTreeClassifier:
    model.fit(X_train, y_train)
    return model
