try:
    import plotly  # noqa: F401
except ImportError:
    pass
else:
    # Sematic
    import sematic.types.types.plotly.figure  # noqa: F401
