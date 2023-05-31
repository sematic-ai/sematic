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
    name = "flan_t5_finetune",
    requirements = pip_deps,
)
