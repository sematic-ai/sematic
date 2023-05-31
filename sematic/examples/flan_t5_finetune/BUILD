load("//bazel:pipeline.bzl", "sematic_pipeline")

# pip_deps = [
#     "accelerate",
#     "datasets",
#     "huggingface-hub",
#     "peft",
#     "torch",
#     "transformers",
# ]

# sematic_example(
#     name = "flan_t5_finetune",
#     requirements = pip_deps,
# )


# py_library(
#     name = "flan_t5_finetune_pipeline_lib",
#     srcs = glob([
#         "*.py",
#         "**/*.py",
#     ]),
#     deps = [
#         "//sematic:init",
#     ] + [
#         requirement(pip_dep) for pip_dep in pip_deps
#     ],
# )

# sematic_pipeline(
#     name = "flan_t5_finetune",
#     dev = True,
#     base = "@sematic-worker-cuda//image",
#     registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com",
#     repository = "sematic-dev",
#     deps = [
#         ":flan_t5_finetune_lib",
#     ],
# )
