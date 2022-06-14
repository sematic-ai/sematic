try:
    import matplotlib  # noqa: F401
except ImportError:
    pass
else:
    import sematic.types.types.matplotlib.figure  # noqa: F401
