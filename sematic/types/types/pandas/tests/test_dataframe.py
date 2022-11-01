# Third-party
# Standard Library
import datetime
import json
import os

# Third-party
import pandas

# Sematic
from sematic.db.models.factories import make_artifact
from sematic.types.serialization import (
    get_json_encodable_summary,
    type_from_json_encodable,
    type_to_json_encodable,
)


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


def test_dataframe_datetime():
    timestamp = datetime.datetime.now()
    df = pandas.DataFrame([dict(a=timestamp)])

    artifact = make_artifact(df, pandas.DataFrame)

    assert json.loads(artifact.json_summary)["dataframe"] == {
        "a": {"0": str(timestamp)}
    }


def test_type_from_json_encodable():
    json_encodable = type_to_json_encodable(pandas.DataFrame)
    assert type_from_json_encodable(json_encodable) is pandas.DataFrame
