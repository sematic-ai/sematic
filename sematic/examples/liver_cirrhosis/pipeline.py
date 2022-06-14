# Standard library
from dataclasses import dataclass

# Third-party
import pandas as pd
import matplotlib.figure
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold
import numpy as np
import sklearn
from sklearn.metrics import roc_auc_score
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import precision_recall_curve
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

# Sematic
import sematic


@sematic.func
def load_data(csv_path: str) -> pd.DataFrame:
    """
    Load CSV file into a DataFrame.
    """
    return pd.read_csv(csv_path, index_col="ID")


@sematic.func
def fill_na(df: pd.DataFrame) -> pd.DataFrame:
    """
    With such a small dataset, we cannot afford to remove data with missing values.

    For numerical values, we fill with the median of the column.
    For categorical values, we fill with the most frequent value.
    """
    df_num_col = df.select_dtypes(include=(["int64", "float64"])).columns
    for c in df_num_col:
        df[c].fillna(df[c].median(), inplace=True)

    df_cat_col = df.select_dtypes(include=("object")).columns
    for c in df_cat_col:
        df[c].fillna(df[c].mode().values[0], inplace=True)

    return df


@sematic.func
def plot_stage_counts(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """
    Generate distribution of stages
    """
    figure = plt.figure()
    sns.countplot(y=df["Stage"], palette="flare", alpha=0.8)
    return figure


@sematic.func
def plot_disease_across_features(df: pd.DataFrame) -> matplotlib.figure.Figure:
    figure = plt.figure(figsize=(21.2, 10))

    plt.subplot(2, 3, 1)
    sns.countplot(x=df["Stage"], hue=df["Sex"], palette="Blues", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Disease Stage Across Gender")

    plt.subplot(2, 3, 2)
    sns.countplot(x=df["Stage"], hue=df["Ascites"], palette="Purples", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Ascites proportion across Stages")

    plt.subplot(2, 3, 3)
    sns.countplot(x=df["Stage"], hue=df["Drug"], palette="Blues", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Medications prescribed across Stages")

    plt.subplot(2, 3, 4)
    sns.countplot(x=df["Stage"], hue=df["Hepatomegaly"], palette="Purples", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Hepatomegaly")

    plt.subplot(2, 3, 5)
    sns.countplot(x=df["Stage"], hue=df["Spiders"], palette="Blues", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Presence of Spiders across stages")

    plt.subplot(2, 3, 6)
    sns.countplot(x=df["Stage"], hue=df["Edema"], palette="Purples", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Edema")

    return figure


@sematic.func
def plot_feature_distributions(df: pd.DataFrame) -> matplotlib.figure.Figure:
    figure = plt.figure(figsize=(20.6, 15))

    plt.subplot(3, 3, 1)
    sns.kdeplot(df["Cholesterol"], hue=df["Stage"], fill=True, palette="Purples")
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Cholesterol Distribution in stages")

    plt.subplot(3, 3, 2)
    sns.kdeplot(
        df["Bilirubin"], hue=df["Stage"], fill=True, palette="Blues", common_norm=True
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Bilirubin")

    plt.subplot(3, 3, 3)
    sns.kdeplot(
        df["Tryglicerides"],
        hue=df["Stage"],
        fill=True,
        palette="Purples",
        common_norm=True,
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Tryglicerides")

    plt.subplot(3, 3, 4)
    sns.kdeplot(
        df["Age"], hue=df["Stage"], fill=True, palette="Blues", common_norm=True
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Age Distribution in stages")

    plt.subplot(3, 3, 5)
    sns.kdeplot(
        df["Prothrombin"],
        hue=df["Stage"],
        fill=True,
        palette="Purples",
        common_norm=True,
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Prothrombin")

    plt.subplot(3, 3, 6)
    sns.kdeplot(
        df["Copper"], hue=df["Stage"], fill=True, palette="Blues", common_norm=True
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Copper")

    plt.subplot(3, 3, 7)
    sns.kdeplot(df["Platelets"], hue=df["Stage"], fill=True, palette="Purples")
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Platelets in stages")

    plt.subplot(3, 3, 8)
    sns.kdeplot(
        df["Albumin"], hue=df["Stage"], fill=True, palette="Blues", common_norm=True
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Albumin")

    plt.subplot(3, 3, 9)
    sns.kdeplot(
        df["SGOT"], hue=df["Stage"], fill=True, palette="Purples", common_norm=True
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("SGOT")

    return figure


@sematic.func
def plot_positive_correlations(df: pd.DataFrame) -> matplotlib.figure.Figure:
    figure = plt.figure(figsize=(21, 12))

    plt.subplot(3, 1, 1)
    sns.regplot(
        x=df["Age"], y=df["Stage"], scatter=False, logistic=False, color="royalblue"
    )
    sns.despine(
        fig=None,
        ax=None,
        top=True,
        right=True,
        left=True,
        bottom=True,
        offset=None,
        trim=False,
    )
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.ylabel("Cirrhosis Probability")
    plt.setp(
        plt.title("Cirrhosis Probability with increasing Age(in days)"),
        color="royalblue",
    )

    plt.subplot(3, 1, 2)
    sns.regplot(
        x=df["Prothrombin"],
        y=df["Stage"],
        scatter=False,
        logistic=False,
        color="orchid",
    )
    sns.despine(
        fig=None,
        ax=None,
        top=True,
        right=True,
        left=True,
        bottom=True,
        offset=None,
        trim=False,
    )
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.ylabel("Cirrhosis Probability")
    plt.setp(
        plt.title("Cirrhosis Probability with increasing Prothrombin Content"),
        color="darkmagenta",
    )

    plt.subplot(3, 1, 3)
    sns.regplot(
        x=df["Copper"], y=df["Stage"], scatter=False, logistic=False, color="royalblue"
    )
    sns.despine(
        fig=None,
        ax=None,
        top=True,
        right=True,
        left=True,
        bottom=True,
        offset=None,
        trim=False,
    )
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.ylabel("Cirrhosis Probability")
    plt.setp(
        plt.title("Cirrhosis Probability with increasing Copper Accumulation"),
        color="royalblue",
    )

    return figure


@sematic.func
def plot_negative_correlations(df: pd.DataFrame) -> matplotlib.figure.Figure:
    figure = plt.figure(figsize=(21, 12))

    plt.subplot(3, 1, 1)
    sns.regplot(
        x=df["Platelets"], y=df["Stage"], scatter=False, logistic=False, color="orchid"
    )
    sns.despine(
        fig=None,
        ax=None,
        top=True,
        right=True,
        left=True,
        bottom=True,
        offset=None,
        trim=False,
    )
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.ylabel("Cirrhosis Probability")
    plt.setp(plt.title("Cirrhosis Probability with Platelets"), color="darkmagenta")

    plt.subplot(3, 1, 2)
    sns.regplot(
        x=df["Albumin"], y=df["Stage"], scatter=False, logistic=False, color="royalblue"
    )
    sns.despine(
        fig=None,
        ax=None,
        top=True,
        right=True,
        left=True,
        bottom=True,
        offset=None,
        trim=False,
    )
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.ylabel("Cirrhosis Probability")
    plt.setp(plt.title("Cirrhosis Probability with Albumin Content"), color="royalblue")

    plt.subplot(3, 1, 3)
    sns.regplot(
        x=df["Cholesterol"],
        y=df["Stage"],
        scatter=False,
        logistic=False,
        color="orchid",
    )
    sns.despine(
        fig=None,
        ax=None,
        top=True,
        right=True,
        left=True,
        bottom=True,
        offset=None,
        trim=False,
    )
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.ylabel("Cirrhosis Probability")
    plt.setp(plt.title("Cirrhosis Probability Cholesterol"), color="darkmagenta")

    return figure


@dataclass
class TrainingData:
    X: pd.DataFrame
    y: pd.Series


@sematic.func
def pre_processing(df: pd.DataFrame) -> TrainingData:
    # replacing catagorical data with integers.
    df = df.copy()
    df["Sex"] = df["Sex"].replace({"M": 0, "F": 1})  # Male : 0 , Female :1
    df["Ascites"] = df["Ascites"].replace({"N": 0, "Y": 1})  # N : 0, Y : 1
    df["Drug"] = df["Drug"].replace(
        {"D-penicillamine": 0, "Placebo": 1}
    )  # D-penicillamine : 0, Placebo : 1
    df["Hepatomegaly"] = df["Hepatomegaly"].replace({"N": 0, "Y": 1})  # N : 0, Y : 1
    df["Spiders"] = df["Spiders"].replace({"N": 0, "Y": 1})  # N : 0, Y : 1
    df["Edema"] = df["Edema"].replace({"N": 0, "Y": 1, "S": -1})  # N : 0, Y : 1, S : -1
    df["Status"] = df["Status"].replace(
        {"C": 0, "CL": 1, "D": -1}
    )  # 'C':0, 'CL':1, 'D':-1

    X = df.drop(["Status", "N_Days", "Stage"], axis=1)
    y: pd.Series = df.pop("Stage")

    # le = LabelEncoder()
    # y = le.fit_transform(y)

    return TrainingData(X=X, y=y)


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
    le = LabelEncoder()
    y = le.fit_transform(y)

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

    training_data = pre_processing(df)

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
