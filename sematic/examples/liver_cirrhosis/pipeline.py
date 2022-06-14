# Standard library
from dataclasses import dataclass

# Third-party
import pandas as pd
import matplotlib.figure
import matplotlib.pyplot as plt
import seaborn as sns

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

    return TrainingData(X=X, y=y)


@dataclass
class PipelineOutput:
    stage_counts: matplotlib.figure.Figure
    disease_across_features: matplotlib.figure.Figure
    feature_distributions: matplotlib.figure.Figure
    positive_correlations: matplotlib.figure.Figure
    negative_correlations: matplotlib.figure.Figure


@sematic.func
def make_output(
    stage_counts: matplotlib.figure.Figure,
    disease_across_features: matplotlib.figure.Figure,
    feature_distributions: matplotlib.figure.Figure,
    positive_correlations: matplotlib.figure.Figure,
    negative_correlations: matplotlib.figure.Figure,
) -> PipelineOutput:
    return PipelineOutput(
        stage_counts=stage_counts,
        disease_across_features=disease_across_features,
        feature_distributions=feature_distributions,
        positive_correlations=positive_correlations,
        negative_correlations=negative_correlations,
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

    return make_output(
        stage_counts=stage_counts,
        disease_across_features=disease_across_features,
        feature_distributions=feature_distributions,
        positive_correlations=positive_correlations,
        negative_correlations=negative_correlations,
    )
