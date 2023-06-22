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
    extras = ["//sematic/ee:metrics"]
)
