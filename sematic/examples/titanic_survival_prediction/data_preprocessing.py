# Third-party
import pandas as pd
from typing import Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import fetch_openml
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split

# Sematic
import sematic

# Titianic survival prediction example
import sematic.examples.titanic_survival_prediction.consts as consts


def remove_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # remove high missing value columns
    df.drop(["cabin", "boat", "body"], axis=1, inplace=True)

    # remove less interesting features
    df.drop(["name", "ticket", "home.dest"], axis=1, inplace=True)

    return df


def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    parameters = {}
    for col in df.columns[df.isnull().any()]:
        if (
            df[col].dtype == "float64"
            or df[col].dtype == "int64"
            or df[col].dtype == "int32"
        ):
            strategy = "mean"
        else:
            strategy = "most_frequent"
        missing_values = df[col][df[col].isnull()].values[0]
        parameters[col] = {"missing_values": missing_values, "strategy": strategy}

    for col, param in parameters.items():
        missing_values = param["missing_values"]
        strategy = param["strategy"]
        imp = SimpleImputer(missing_values=missing_values, strategy=strategy)
        df[col] = imp.fit_transform(df[[col]])

    return df


def categorical_to_numerical(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    dummies = pd.get_dummies(df[cat_cols], drop_first=True)
    df[dummies.columns] = dummies
    df.drop(cat_cols, axis=1, inplace=True)
    return df


def scale_numerical_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Select numerical columns
    num_cols = df.select_dtypes(include=["int64", "float64", "int32"]).columns

    # Apply StandardScaler
    scaler = StandardScaler()
    df[num_cols] = scaler.fit_transform(df[num_cols])
    return df


@sematic.func
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    X, y = fetch_openml("titanic", version=1, as_frame=True, return_X_y=True)
    return X, y


@sematic.func
def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = remove_columns(df)
    df = fill_missing_values(df)
    df = categorical_to_numerical(df)
    df = scale_numerical_data(df)
    return df


@sematic.func
def split_data(
    df_X: pd.DataFrame, df_y: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    X_train, X_test, y_train, y_test = train_test_split(
        df_X, df_y, test_size=0.3, random_state=consts.RAND_STATE
    )
    return X_train, y_train, X_test, y_test
