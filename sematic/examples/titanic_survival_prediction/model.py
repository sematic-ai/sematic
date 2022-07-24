# Third-party
from sklearn.tree import DecisionTreeClassifier

# Sematic
import sematic

# Titianic survival prediction example
import sematic.examples.titanic_survival_prediction.consts as consts


@sematic.func
def init_model() -> DecisionTreeClassifier:
    return DecisionTreeClassifier(
        random_state=consts.RAND_STATE,
        class_weight=consts.DECISION_TREE_CLASS_WEIGHT,
        max_depth=consts.DECISION_TREE_MAX_DEPTH,
    )
