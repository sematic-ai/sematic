try:
    # Third-party
    import matplotlib  # noqa: F401
except ImportError:
    print("NO MATPLOTLIB")
    pass
else:
    print("YES MATPLOTLIB")
    # Sematic
    import sematic.types.types.matplotlib.figure  # noqa: F401
