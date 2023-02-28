export default {
    "cache_key": null,
    "calculator_path": "sematic.examples.add.pipeline.pipeline",
    "container_image_uri": null,
    "created_at": new Date("2023-02-03T16:51:47.578632+00:00"),
    "description": "## This is the docstring\n\nA trivial pipeline to showcase basic future encapsulation.\n\nThis pipeline simply adds a bunch of numbers. It shows how calculators can\nbe arbitrarily nested.\n\n### It supports markdown\n\n`pretty_cool`.",
    "ended_at": new Date("2023-02-03T16:51:47.746584+00:00"),
    "exception_metadata_json": null,
    "external_exception_metadata_json": null,
    "external_jobs_json": null,
    "failed_at": null,
    "future_state": "RESOLVED",
    "id": "e5a0aca06816414fa6fd2ffa0649ea6d",
    "name": "Basic add example pipeline",
    "nested_future_id": "dc9203e31c764656a424a2c274ba40c0",
    "original_run_id": null,
    "parent_id": null,
    "resolved_at": new Date("2023-02-03T16:52:13.146034+00:00"),
    "resource_requirements_json": null,
    "root_id": "e5a0aca06816414fa6fd2ffa0649ea6d",
    "source_code": "@sematic.func\ndef pipeline(a: float, b: float, c: float) -> float:\n    \"\"\"\n    ## This is the docstring\n\n    A trivial pipeline to showcase basic future encapsulation.\n\n    This pipeline simply adds a bunch of numbers. It shows how calculators can\n    be arbitrarily nested.\n\n    ### It supports markdown\n\n    `pretty_cool`.\n    \"\"\"\n    sum1 = add(a, b)\n    sum2 = add(b, c)\n    sum3 = add(a, c)\n    return add3(sum1, sum2, sum3)\n",
    "started_at": new Date("2023-02-03T16:51:47.732288+00:00"),
    "tags": [
        "example",
        "basic",
        "final"
    ],
    "updated_at": new Date("2023-02-03T16:51:47.578636+00:00")
}
