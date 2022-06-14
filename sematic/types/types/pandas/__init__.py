try:
    import pandas  # noqa: F401
except ImportError:
    pass
else:
    import sematic.types.types.pandas.dataframe  # noqa: F401
