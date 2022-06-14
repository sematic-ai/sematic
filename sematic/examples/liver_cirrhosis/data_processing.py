# Standard library
from dataclasses import dataclass

# Third-party
import pandas as pd
from sklearn.preprocessing import LabelEncoder

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


@dataclass
class TrainingData:
    X: pd.DataFrame
    y: pd.Series


@sematic.func
def pre_process(df: pd.DataFrame) -> TrainingData:
    """
    Standardize and prepare data for training.
    """
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

    le = LabelEncoder()
    y = le.fit_transform(y)

    return TrainingData(X=X, y=y)
