try:
    # Third-party
    import torch  # noqa: F401
except ImportError:
    pass
else:
    # Sematic
    import sematic.types.types.pytorch.dataloader  # noqa: F401
    import sematic.types.types.pytorch.module  # noqa: F401
