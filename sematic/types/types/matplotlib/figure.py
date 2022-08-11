# Standard Library
import os
import uuid
from typing import Any

# Third-party
import matplotlib.figure  # type: ignore

# Sematic
from sematic.config import get_config
from sematic.types.registry import register_to_json_encodable_summary


@register_to_json_encodable_summary(matplotlib.figure.Figure)
def _mpl_figure_summary(value: matplotlib.figure.Figure, _) -> Any:
    # TODO: use use artifact binary repr for this instead of by hand
    filename = uuid.uuid4().hex
    path = os.path.join(get_config().data_dir, filename)
    value.savefig(path)

    return {"path": "/data/{}.png".format(filename)}
