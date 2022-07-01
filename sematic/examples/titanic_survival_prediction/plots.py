# Data class
from sematic.examples.titanic_survival_prediction.data_classes import TrainTestData

# Third-party
import pandas as pd
import matplotlib.figure
import matplotlib.pyplot as plt
import seaborn as sns

# Sematic
import sematic

def plot_missing_values(df: pd.DataFrame) -> matplotlib.figure.Figure:
    figure = plt.figure()
    miss_vals = pd.DataFrame(df.isnull().sum() / len(df) * 100)
    sns.barplot(
        data=miss_vals
    )
    return figure

@sematic.func
def make_eda_plots(feature_label_dataframes: TrainTestData) -> matplotlib.figure.Figure:
    df_X, df_y = feature_label_dataframes.train_data, feature_label_dataframes.test_data
    df = pd.concat([df_X, df_y], axis=1)
    return plot_missing_values(df)
