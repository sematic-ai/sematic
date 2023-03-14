sematic_py_lib(
    name = "artifact",
    srcs = ["artifact.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        "//sematic/db/models/mixins:json_encodable_mixin",
    ],
)

sematic_py_lib(
    name = "base",
    srcs = ["base.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [],
)

sematic_py_lib(
    name = "factories",
    srcs = ["factories.py"],
    deps = [
        ":artifact",
        ":edge",
        ":resolution",
        ":run",
        ":user",
        "//sematic:abstract_future",
        "//sematic/types:serialization",
        "//sematic/types/types:union",
        "//sematic/utils:hashing",
        "//sematic/utils:json",
    ],
)

sematic_py_lib(
    name = "edge",
    srcs = ["edge.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        "//sematic/db/models/mixins:json_encodable_mixin",
    ],
)

sematic_py_lib(
    name = "external_resource",
    srcs = ["external_resource.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        "//sematic/db/models/mixins:json_encodable_mixin",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/types:serialization",
    ],
)

sematic_py_lib(
    name = "git_info",
    srcs = ["git_info.py"],
    pip_deps = [],
    deps = [
        ":base",
    ],
)

sematic_py_lib(
    name = "job",
    srcs = ["job.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        "//sematic/db/models/mixins:json_encodable_mixin",
        "//sematic/scheduling:job_details",
        "//sematic/types/types:dataclass",
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name = "run",
    srcs = ["run.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        "//sematic:abstract_calculator",
        "//sematic:abstract_future",
        "//sematic/db/models/mixins:has_external_jobs_mixin",
        "//sematic/db/models/mixins:has_user_mixin",
        "//sematic/db/models/mixins:json_encodable_mixin",
        "//sematic/scheduling:external_job",
        "//sematic/types:serialization",
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name = "runs_external_resource",
    srcs = ["runs_external_resource.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        "//sematic/db/models/mixins:json_encodable_mixin",
    ],
)

sematic_py_lib(
    name = "resolution",
    srcs = ["resolution.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        ":git_info",
        "//sematic/db/models/mixins:has_external_jobs_mixin",
        "//sematic/db/models/mixins:has_user_mixin",
        "//sematic/db/models/mixins:json_encodable_mixin",
    ],
)

sematic_py_lib(
    name = "note",
    srcs = ["note.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        "//sematic/db/models/mixins:has_user_mixin",
        "//sematic/db/models/mixins:json_encodable_mixin",
    ],
)

sematic_py_lib(
    name = "user",
    srcs = ["user.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        "//sematic/db/models/mixins:json_encodable_mixin",
    ],
)
