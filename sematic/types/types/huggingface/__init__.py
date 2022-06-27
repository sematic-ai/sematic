try:
    import transformers  # noqa: F401
except ImportError:
    pass
else:
    import sematic.types.types.huggingface.training_arguments  # noqa: F401
