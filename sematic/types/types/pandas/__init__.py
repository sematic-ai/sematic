try:
    import pandas  # noqa: F401
except ImportError:
    pass
else:
    # Sematic
    import sematic.types.types.pandas.dataframe  # noqa: F401
