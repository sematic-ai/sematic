try:
    # Third-party
    import PIL  # noqa: F401
except ImportError:
    pass
else:
    # Sematic
    import sematic.types.types.PIL.image  # noqa: F401
