# Third-party
import matplotlib.figure
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Sematic
import sematic
from sematic.examples.titanic_survival_prediction.data_classes import EDAPlots


def plot_missing_values(df: pd.DataFrame) -> matplotlib.figure.Figure:
    figure = plt.figure()
    miss_vals = pd.DataFrame(df.isnull().sum() / len(df) * 100)
    miss_vals.plot(
        kind="bar", title="Missing values in percentage", ylabel="percentage"
    )
    return figure


def plot_survival_gender(df: pd.DataFrame) -> matplotlib.figure.Figure:
    figure = plt.figure()
    df["survived"] = df.survived.astype("int")
    sns.barplot(x="sex", y="survived", data=df)
    return figure


def plot_survival_by_class(df: pd.DataFrame) -> matplotlib.figure.Figure:
    figure = plt.figure()
    sns.countplot(x="pclass", data=df)
    return figure


@sematic.func
def make_eda_plots(df_X: pd.DataFrame, df_y: pd.DataFrame) -> EDAPlots:
    df = pd.concat([df_X, df_y], axis=1)
    survival_gender_figure = plot_survival_gender(df)
    survival_class_figure = plot_survival_by_class(df)
    return EDAPlots(survival_gender_figure, survival_class_figure)
