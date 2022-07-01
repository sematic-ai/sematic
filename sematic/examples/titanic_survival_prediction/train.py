# Data class
from sematic.examples.titanic_survival_prediction.data_classes import TrainTestSplit

# Sematic
import sematic

# Third-party
from sklearn.tree import DecisionTreeClassifier

@sematic.func
def train_model(model: DecisionTreeClassifier, train_test_split_dataframes: TrainTestSplit) -> DecisionTreeClassifier:
    X_train, y_train = train_test_split_dataframes.train_features, train_test_split_dataframes.train_labels
    model.fit(X_train, y_train)
    return model