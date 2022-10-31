# Third-party
import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Sematic
import sematic


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
    sns.countplot(data=df, x="Stage", hue="Sex", palette="Blues", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Disease Stage Across Gender")

    plt.subplot(2, 3, 2)
    sns.countplot(data=df, x="Stage", hue="Ascites", palette="Purples", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Ascites proportion across Stages")

    plt.subplot(2, 3, 3)
    sns.countplot(data=df, x="Stage", hue="Drug", palette="Blues", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Medications prescribed across Stages")

    plt.subplot(2, 3, 4)
    sns.countplot(data=df, x="Stage", hue="Hepatomegaly", palette="Purples", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Hepatomegaly")

    plt.subplot(2, 3, 5)
    sns.countplot(data=df, x="Stage", hue="Spiders", palette="Blues", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Presence of Spiders across stages")

    plt.subplot(2, 3, 6)
    sns.countplot(data=df, x="Stage", hue="Edema", palette="Purples", alpha=0.9)
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Edema")

    return figure


@sematic.func
def plot_feature_distributions(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """
    Plotting distribution of model features.

    ### Parameters
    df: `pd.Dataframe`

    ### Returns
    `matplotlib.figure.Figure`
    """
    figure = plt.figure(figsize=(20.6, 15))

    plt.subplot(3, 3, 1)
    sns.kdeplot(data=df, x="Cholesterol", hue="Stage", fill=True, palette="Purples")
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Cholesterol Distribution in stages")

    plt.subplot(3, 3, 2)
    sns.kdeplot(
        data=df,
        x="Bilirubin",
        hue="Stage",
        fill=True,
        palette="Blues",
        common_norm=True,
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Bilirubin")

    plt.subplot(3, 3, 3)
    sns.kdeplot(
        data=df,
        x="Tryglicerides",
        hue="Stage",
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
        data=df, x="Age", hue="Stage", fill=True, palette="Blues", common_norm=True
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Age Distribution in stages")

    plt.subplot(3, 3, 5)
    sns.kdeplot(
        data=df,
        x="Prothrombin",
        hue="Stage",
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
        data=df, x="Copper", hue="Stage", fill=True, palette="Blues", common_norm=True
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Copper")

    plt.subplot(3, 3, 7)
    sns.kdeplot(data=df, x="Platelets", hue="Stage", fill=True, palette="Purples")
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Platelets in stages")

    plt.subplot(3, 3, 8)
    sns.kdeplot(
        data=df, x="Albumin", hue="Stage", fill=True, palette="Blues", common_norm=True
    )
    sns.despine(top=True, right=True, bottom=True, left=True)
    plt.tick_params(axis="both", which="both", bottom=False, top=False, left=False)
    plt.xlabel("")
    plt.title("Albumin")

    plt.subplot(3, 3, 9)
    sns.kdeplot(
        data=df, x="SGOT", hue="Stage", fill=True, palette="Purples", common_norm=True
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
