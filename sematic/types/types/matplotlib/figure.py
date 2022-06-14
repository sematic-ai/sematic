# Standard library
import os
from typing import Any
import uuid

# Third-party
import matplotlib.figure  # type: ignore

# Sematic
from sematic.types.registry import register_to_json_encodable_summary
from sematic.config import get_config


@register_to_json_encodable_summary(matplotlib.figure.Figure)
def _mpl_figure_summary(value: matplotlib.figure.Figure, _) -> Any:
    # TODO: use use artifact binary repr for this instead of by hand
    filename = uuid.uuid4().hex
    path = os.path.join(get_config().data_dir, filename)
    value.savefig(path)

    return {"path": "/data/{}.png".format(filename)}
