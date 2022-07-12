# Standard library
import json
from typing import Any

# Third party
import pandas


# Sematic
from sematic.types.registry import register_to_json_encodable_summary


_PAYLOAD_CUTOFF = 3000


@register_to_json_encodable_summary(pandas.DataFrame)
def _dataframe_json_encodable_summary(value: pandas.DataFrame, _) -> Any:
    truncated = False
    payload: Any = value.to_dict()
    index = list(value.index)

    if len(json.dumps(payload, default=str)) > _PAYLOAD_CUTOFF:
        payload = value.head().to_dict()
        index = index[: len(value.head())]
        truncated = True

    # We want to preserve the order of the columns
    dtypes = [
        (name, dtype.name) for name, dtype in zip(value.dtypes.index, value.dtypes)
    ]

    describe = []
    try:
        describe = value.describe().to_dict()  # type: ignore  # (pandas stubs bug)
    except ValueError:
        pass

    return dict(
        dataframe=payload,
        index=index,
        dtypes=dtypes,
        truncated=truncated,
        shape=value.shape,
        describe=describe,
        isna=value.isna().sum().to_dict(),
    )
