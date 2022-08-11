# Standard Library
from dataclasses import dataclass

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import sklearn

# Third-party
from sklearn.metrics import (
    auc,
    classification_report,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold

# Sematic
import sematic

# Liver cirrhosis
from sematic.examples.liver_cirrhosis.data_processing import TrainingData


@dataclass
class TrainingOutput:
    mean_accuracy: float
    classification_report: str
    auc: float
    pr_curve: matplotlib.figure.Figure


@sematic.func
def train_model(
    model: sklearn.base.BaseEstimator, training_data: TrainingData
) -> TrainingOutput:
    X, y = training_data.X, training_data.y

    skf = StratifiedKFold(n_splits=10, random_state=1, shuffle=True)

    acc = []

    def _training(train, test, fold_no):
        X_train = train
        # y_train = y.iloc[train_index]
        y_train = y[train_index]
        X_test = test
        y_test = y[test_index]  # y.iloc[test_index]
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)
        acc.append(score)
        print("For Fold {} the accuracy is {}".format(str(fold_no), score))

    fold_no = 1
    for train_index, test_index in skf.split(X, y):
        train = X.iloc[train_index, :]
        test = X.iloc[test_index, :]
        _training(train, test, fold_no)
        fold_no += 1

    log_model_predict = model.predict(test)
    log_model_predict_proba = model.predict_proba(test)

    # classif_report = classification_report(y.iloc[test_index], log_model_predict)
    classif_report = classification_report(y[test_index], log_model_predict)

    auc_ = roc_auc_score(y[test_index], log_model_predict_proba, multi_class="ovr")

    # fpr, tpr, threshold = roc_curve(y.iloc[test_index], log_model_predict_proba[:, 1])
    fpr, tpr, threshold = roc_curve(
        y[test_index], log_model_predict_proba[:, 1], pos_label=1
    )
    roc_auc = auc(fpr, tpr)

    sns.set_style("whitegrid")
    pr_curve = plt.figure(figsize=(21, 6))

    plt.subplot(1, 2, 1)
    plt.title("Receiver Operating Characteristic")
    sns.lineplot(
        x=fpr, y=tpr, label="AUC = %0.2f" % roc_auc, palette="purple", linewidth=3
    )
    plt.legend(loc="lower right")
    plt.plot([0, 1], [0, 1], "r--")
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.ylabel("True Positive Rate")
    plt.xlabel("False Positive Rate")
    plt.tick_params(left=False, bottom=False)
    sns.despine(top=True, bottom=True, left=True)

    # calculate precision-recall curve
    precision, recall, thresholds = precision_recall_curve(
        y[test_index], log_model_predict_proba[:, 1], pos_label=1
    )

    plt.subplot(1, 2, 2)
    plt.plot(precision, recall, linewidth=3, color="orchid")
    sns.despine(top=True, bottom=True, left=True)
    plt.xlabel("Precision")
    plt.ylabel("Recall")
    plt.title("Precision Recall Curve")

    return TrainingOutput(
        mean_accuracy=np.mean(acc),
        classification_report=classif_report,
        auc=auc_,
        pr_curve=pr_curve,
    )
