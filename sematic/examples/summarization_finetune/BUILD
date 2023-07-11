load("//bazel:pipeline.bzl", "sematic_pipeline")

pip_deps = [
    # Note that this does not exactly match the
    # requirements in the example's requirements.txt.
    # This is because bazel isn't playing nicely with
    # all of the reqs in the requirements.txt.
    # You should check on this again later, once there
    # are newer versions of the libs.
    "accelerate",
    "datasets",
    "gradio",
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
