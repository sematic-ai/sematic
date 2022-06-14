# Third-party
import os
import pandas

# Sematic
from sematic.types.serialization import get_json_encodable_summary


def test_dataframe_summary():
    df = pandas.read_csv(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "cirrhosis.csv"),
        index_col=["ID"],
    )

    summary = get_json_encodable_summary(df, pandas.DataFrame)
    assert summary["shape"] == df.shape
    assert len(summary["dataframe"]) == 19
    assert len(list(summary["dataframe"].values())[0]) == 5
    assert len(summary["describe"]) == 12
    assert len(summary["isna"]) == 19
