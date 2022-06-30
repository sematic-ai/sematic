"""
Sematic Types public API

Only types with lightweight dependencies should
be added here. Ideally only standard library.
"""
import sematic.types.types.bool  # noqa: F401
import sematic.types.types.dataclass  # noqa: F401
import sematic.types.types.integer  # noqa: F401
import sematic.types.types.list  # noqa: F401
import sematic.types.types.tuple  # noqa: F401
import sematic.types.types.dict  # noqa: F401
import sematic.types.types.float  # noqa: F401
import sematic.types.types.none  # noqa: F401
import sematic.types.types.union  # noqa: F401
import sematic.types.types.str  # noqa: F401
from sematic.types.types.float_in_range import FloatInRange  # noqa: F401


# PyTorch
# Only activates if torch is available
import sematic.types.types.pytorch  # noqa: F401


# Plotly
# Only activates if plotly is available
import sematic.types.types.plotly  # noqa: F401


# Pandas
# Only activates if pandas is available
import sematic.types.types.pandas  # noqa: F401

# Matplotlib
# Only activates if matplotlib is available
import sematic.types.types.matplotlib  # noqa: F401
