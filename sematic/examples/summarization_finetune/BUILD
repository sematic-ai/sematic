load("//bazel:pipeline.bzl", "sematic_pipeline")

pip_deps = [
    "accelerate",
    "bitsandbytes",
    "datasets",
    "einops",
    "huggingface-hub",
    "nvidia-cusparse-cu11",
    "peft",
    "scipy",
    "torch",
    "transformers",
]

sematic_example(
    name = "summarization_finetune",
    requirements = pip_deps,
    extras = ["//sematic/ee:metrics"]
)
