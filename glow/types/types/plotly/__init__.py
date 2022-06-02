try:
    import plotly  # noqa: F401
except ImportError:
    pass
else:
    import glow.types.types.plotly.figure  # noqa: F401
