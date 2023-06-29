load("//bazel:pipeline.bzl", "sematic_pipeline")

pip_deps = [
    "accelerate",
    "datasets",
    "huggingface-hub",
    "peft",
    "torch",
    "transformers",
]

sematic_example(
    name = "summarization_finetune",
    requirements = pip_deps,
    # Uncomment to allow running with metrics; must also
    # uncomment import in train_eval
    # extras = ["//sematic/ee:metrics"]
)
