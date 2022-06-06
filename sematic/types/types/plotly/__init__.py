try:
    import plotly  # noqa: F401
except ImportError:
    pass
else:
    import sematic.types.types.plotly.figure  # noqa: F401
