"""
A copy of 
https://github.com/bazelbuild/rules_python/blob/main/python/packaging.bzl
to patch some odd behavior.

- The native py_wheel behavior will only pack source files for direct dependencies,
not transitive. For this purpose, py_package is to be used. Since we are redefining py_wheel
here, might as well include that behavior natively.

- py_package by default packages all source files including those of third-party dependencies
that were installed by pip_parse. To remedy this, py_package offers a packages arguments that
allows filtering. We bake this into sematic_py_wheel for an easier API

- Finally, and the REAL reason why we do this, is that the native py_wheel needs a hardcoded list
of "requires" dependencies. When working in a monorepo that is not quite practical, since requirements
are managed centrally (one requirements.in for all projects). Having to hard-code requirements in the BUILD
file leads to desynchronization. This patch automatically extract wheels necessary for the source files
being packaged in the wheel. This is nice BUT does not support fixed wheel versions (TODO).

Why not use setup.py like everyone else?
setup.py needs a list of source files to package and a list of dependencies. Because we are in a monorepo,
we don't want to necessarily package ALL files, we also don't want to hard-code a list, or segregate source 
files by in/out of wheel. We have Bazel for this. Each file declares its dependencies and everything is kept
in sync that way.
"""

load("@rules_python//python:packaging.bzl", "PyWheelInfo")
load("//tools:stamp.bzl", "is_stamping_enabled")

_ALWAYS_EXCLUDE_DEPENDENCIES = [
    "pip",
]

def _path_inside_wheel(input_file):
    # input_file.short_path is sometimes relative ("../${repository_root}/foobar")
    # which is not a valid path within a zip file. Fix that.
    short_path = input_file.short_path
    if short_path.startswith("..") and len(short_path) >= 3:
        # Path separator. '/' on linux.
        separator = short_path[2]

        # Consume '../' part.
        short_path = short_path[3:]

        # Find position of next '/' and consume everything up to that character.
        pos = short_path.find(separator)
        short_path = short_path[pos + 1:]
    return short_path

def _input_file_to_arg(input_file):
    """Converts a File object to string for --input_file argument to wheelmaker"""
    return "%s;%s" % (_path_inside_wheel(input_file), input_file.path)

def _escape_filename_segment(segment):
    """Escape a segment of the wheel filename.

    See https://www.python.org/dev/peps/pep-0427/#escaping-and-unicode
    """

    # TODO: this is wrong, isalnum replaces non-ascii letters, while we should
    # not replace them.
    # TODO: replace this with a regexp once starlark supports them.
    escaped = ""
    for character in segment.elems():
        # isalnum doesn't handle unicode characters properly.
        if character.isalnum() or character == ".":
            escaped += character
        elif not escaped.endswith("_"):
            escaped += "_"
    return escaped

def _replace_make_variables(flag, ctx):
    """Replace $(VERSION) etc make variables in flag"""
    if "$" in flag:
        for varname, varsub in ctx.var.items():
            flag = flag.replace("$(%s)" % varname, varsub)
    return flag

def _sematic_py_wheel_impl(ctx):
    version = _replace_make_variables(ctx.attr.version, ctx)
    outfile = ctx.actions.declare_file("-".join([
        _escape_filename_segment(ctx.attr.distribution),
        _escape_filename_segment(version),
        _escape_filename_segment(ctx.attr.python_tag),
        _escape_filename_segment(ctx.attr.abi),
        _escape_filename_segment(ctx.attr.platform),
    ]) + ".whl")

    name_file = ctx.actions.declare_file(ctx.label.name + ".name")

    inputs_to_package = depset(
        direct = ctx.files.deps,
    )

    # START OF PATCH

    requires = list(ctx.attr.requires)
    deps_files = []

    # We handle "ee" and "non-ee" deps distinctly, because we don't want "ee"
    # dependencies to add requirements to the base wheel. Extra third-party
    # deps for ee are all handled via "extra_requires"
    non_ee_deps = [dep for dep in ctx.attr.deps if "sematic/ee" not in dep.label.package]
    non_ee_inputs = depset(
        transitive = [dep[DefaultInfo].data_runfiles.files for dep in non_ee_deps] +
                     [dep[DefaultInfo].default_runfiles.files for dep in non_ee_deps],
    )
    ee_deps = [dep for dep in ctx.attr.deps if "sematic/ee" in dep.label.package]
    ee_inputs = depset(
        transitive = [dep[DefaultInfo].data_runfiles.files for dep in ee_deps] +
                     [dep[DefaultInfo].default_runfiles.files for dep in ee_deps],
    )

    for input_file in non_ee_inputs.to_list():
        file_path = _path_inside_wheel(input_file)
        depedency_name = _extract_dependency_name(file_path)

        if depedency_name != None and depedency_name not in _ALWAYS_EXCLUDE_DEPENDENCIES:
            # Making sure we don't override requires passed manually
            already_in = False
            for require in requires:
                if require.startswith(depedency_name):
                    already_in = True

            if not already_in:
                requires.append(depedency_name)

        if file_path.startswith("sematic"):
            deps_files.append(input_file)

    for input_file in ee_inputs.to_list():
        file_path = _path_inside_wheel(input_file)
        if file_path.startswith("sematic"):
            deps_files.append(input_file)

    inputs_to_package = depset(direct = deps_files)

    # END OF PATCH

    # Inputs to this rule which are not to be packaged.
    # Currently this is only the description file (if used).
    other_inputs = []

    # Wrap the inputs into a file to reduce command line length.
    packageinputfile = ctx.actions.declare_file(ctx.attr.name + "_target_wrapped_inputs.txt")
    content = ""
    for input_file in inputs_to_package.to_list():
        content += _input_file_to_arg(input_file) + "\n"
    ctx.actions.write(output = packageinputfile, content = content)
    other_inputs.append(packageinputfile)

    args = ctx.actions.args()
    args.add("--name", ctx.attr.distribution)
    args.add("--version", version)
    args.add("--python_tag", ctx.attr.python_tag)
    args.add("--abi", ctx.attr.abi)
    args.add("--platform", ctx.attr.platform)
    args.add("--out", outfile)
    args.add("--name_file", name_file)
    args.add_all(ctx.attr.strip_path_prefixes, format_each = "--strip_path_prefix=%s")

    # Pass workspace status files if stamping is enabled
    if is_stamping_enabled(ctx.attr):
        args.add("--volatile_status_file", ctx.version_file)
        args.add("--stable_status_file", ctx.info_file)
        other_inputs.extend([ctx.version_file, ctx.info_file])

    args.add("--input_file_list", packageinputfile)

    # Note: Description file and version are not embedded into metadata.txt yet,
    # it will be done later by wheelmaker script.
    metadata_file = ctx.actions.declare_file(ctx.attr.name + ".metadata.txt")
    metadata_contents = ["Metadata-Version: 2.1"]
    metadata_contents.append("Name: %s" % ctx.attr.distribution)
    metadata_contents.append("Version: %s" % version)

    if ctx.attr.author:
        metadata_contents.append("Author: %s" % ctx.attr.author)
    if ctx.attr.author_email:
        metadata_contents.append("Author-email: %s" % ctx.attr.author_email)
    if ctx.attr.homepage:
        metadata_contents.append("Home-page: %s" % ctx.attr.homepage)
    if ctx.attr.license:
        metadata_contents.append("License: %s" % ctx.attr.license)

    for c in ctx.attr.classifiers:
        metadata_contents.append("Classifier: %s" % c)

    if ctx.attr.python_requires:
        metadata_contents.append("Requires-Python: %s" % ctx.attr.python_requires)
    for requirement in requires:  # PATCHED LINE
        metadata_contents.append("Requires-Dist: %s" % requirement)

    for option, option_requirements in sorted(ctx.attr.extra_requires.items()):
        metadata_contents.append("Provides-Extra: %s" % option)
        for requirement in option_requirements:
            metadata_contents.append(
                "Requires-Dist: %s; extra == '%s'" % (requirement, option),
            )
    ctx.actions.write(
        output = metadata_file,
        content = "\n".join(metadata_contents) + "\n",
    )
    other_inputs.append(metadata_file)
    args.add("--metadata_file", metadata_file)

    # Merge console_scripts into entry_points.
    entrypoints = dict(ctx.attr.entry_points)  # Copy so we can mutate it
    if ctx.attr.console_scripts:
        # Copy a console_scripts group that may already exist, so we can mutate it.
        console_scripts = list(entrypoints.get("console_scripts", []))
        entrypoints["console_scripts"] = console_scripts
        for name, ref in ctx.attr.console_scripts.items():
            console_scripts.append("{name} = {ref}".format(name = name, ref = ref))

    # If any entry_points are provided, construct the file here and add it to the files to be packaged.
    # see: https://packaging.python.org/specifications/entry-points/
    if entrypoints:
        lines = []
        for group, entries in sorted(entrypoints.items()):
            if lines:
                # Blank line between groups
                lines.append("")
            lines.append("[{group}]".format(group = group))
            lines += sorted(entries)
        entry_points_file = ctx.actions.declare_file(ctx.attr.name + "_entry_points.txt")
        content = "\n".join(lines)
        ctx.actions.write(output = entry_points_file, content = content)
        other_inputs.append(entry_points_file)
        args.add("--entry_points_file", entry_points_file)

    if ctx.attr.description_file:
        description_file = ctx.file.description_file
        args.add("--description_file", description_file)
        other_inputs.append(description_file)

    for target, filename in ctx.attr.extra_distinfo_files.items():
        target_files = target.files.to_list()
        if len(target_files) != 1:
            fail(
                "Multi-file target listed in extra_distinfo_files %s",
                filename,
            )
        other_inputs.extend(target_files)
        args.add(
            "--extra_distinfo_file",
            filename + ";" + target_files[0].path,
        )

    ctx.actions.run(
        inputs = depset(direct = other_inputs, transitive = [inputs_to_package]),
        outputs = [outfile, name_file],
        arguments = [args],
        executable = ctx.executable._wheelmaker,
        progress_message = "Building wheel {}".format(ctx.label),
    )
    return [
        DefaultInfo(
            files = depset([outfile]),
            runfiles = ctx.runfiles(files = [outfile]),
        ),
        PyWheelInfo(
            wheel = outfile,
            name_file = name_file,
        ),
    ]


def _extract_dependency_name(path_within_wheel):
    """For a path within the bazel deps, see whether it correponds to a python dep.

    Return that dependency's name if so, otherwise return None.
    """
    # Bazel's build language doesn't support regex:
    # https://community.influxdata.com/t/using-regex-in-starlark/18246
    # will have to implement our own string parsing.
    path_elements = path_within_wheel.split("/")
    if len(path_elements) < 2:
        return None
    if not (path_elements[-1] == "METADATA" and path_elements[-2].endswith("dist-info")):
        return None
    dist_info_path_segment = path_elements[-2]
    depedency_name = dist_info_path_segment.split(".dist-info")[0].split("-")[0].replace("_", "-")
    return depedency_name


def _concat_dicts(*dicts):
    result = {}
    for d in dicts:
        result.update(d)
    return result

_distribution_attrs = {
    "abi": attr.string(
        default = "none",
        doc = "Python ABI tag. 'none' for pure-Python wheels.",
    ),
    "distribution": attr.string(
        mandatory = True,
        doc = """\
Name of the distribution.
This should match the project name onm PyPI. It's also the name that is used to
refer to the package in other packages' dependencies.
""",
    ),
    "platform": attr.string(
        default = "any",
        doc = """\
Supported platform. Use 'any' for pure-Python wheel.
If you have included platform-specific data, such as a .pyd or .so
extension module, you will need to specify the platform in standard
pip format. If you support multiple platforms, you can define
platform constraints, then use a select() to specify the appropriate
specifier, eg:
`
platform = select({
    "//platforms:windows_x86_64": "win_amd64",
    "//platforms:macos_x86_64": "macosx_10_7_x86_64",
    "//platforms:linux_x86_64": "manylinux2014_x86_64",
})
`
""",
    ),
    "python_tag": attr.string(
        default = "py3",
        doc = "Supported Python version(s), eg `py3`, `cp35.cp36`, etc",
    ),
    "stamp": attr.int(
        doc = """\
Whether to encode build information into the wheel. Possible values:
- `stamp = 1`: Always stamp the build information into the wheel, even in \
[--nostamp](https://docs.bazel.build/versions/main/user-manual.html#flag--stamp) builds. \
This setting should be avoided, since it potentially kills remote caching for the target and \
any downstream actions that depend on it.
- `stamp = 0`: Always replace build information by constant values. This gives good build result caching.
- `stamp = -1`: Embedding of build information is controlled by the \
[--[no]stamp](https://docs.bazel.build/versions/main/user-manual.html#flag--stamp) flag.
Stamped targets are not rebuilt unless their dependencies change.
        """,
        default = -1,
        values = [1, 0, -1],
    ),
    "version": attr.string(
        mandatory = True,
        doc = (
            "Version number of the package. Note that this attribute " +
            "supports stamp format strings (eg. `1.2.3-{BUILD_TIMESTAMP}`) " +
            "as well as 'make variables' (e.g. `1.2.3-$(VERSION)`)."
        ),
    ),
    "_stamp_flag": attr.label(
        doc = "A setting used to determine whether or not the `--stamp` flag is enabled",
        default = Label("//:stamp"),
    ),
}

_requirement_attrs = {
    "extra_requires": attr.string_list_dict(
        doc = "List of optional requirements for this package",
    ),
    "requires": attr.string_list(
        doc = ("List of requirements for this package. See the section on " +
               "[Declaring required dependency](https://setuptools.readthedocs.io/en/latest/userguide/dependency_management.html#declaring-dependencies) " +
               "for details and examples of the format of this argument."),
    ),
}

_entrypoint_attrs = {
    "console_scripts": attr.string_dict(
        doc = """\
Deprecated console_script entry points, e.g. `{'main': 'examples.wheel.main:main'}`.
Deprecated: prefer the `entry_points` attribute, which supports `console_scripts` as well as other entry points.
""",
    ),
    "entry_points": attr.string_list_dict(
        doc = """\
entry_points, e.g. `{'console_scripts': ['main = examples.wheel.main:main']}`.
""",
    ),
}

_other_attrs = {
    "author": attr.string(
        doc = "A string specifying the author of the package.",
        default = "",
    ),
    "author_email": attr.string(
        doc = "A string specifying the email address of the package author.",
        default = "",
    ),
    "classifiers": attr.string_list(
        doc = "A list of strings describing the categories for the package. For valid classifiers see https://pypi.org/classifiers",
    ),
    "description_file": attr.label(
        doc = "A file containing text describing the package.",
        allow_single_file = True,
    ),
    "extra_distinfo_files": attr.label_keyed_string_dict(
        doc = "Extra files to add to distinfo directory in the archive.",
        allow_files = True,
    ),
    "homepage": attr.string(
        doc = "A string specifying the URL for the package homepage.",
        default = "",
    ),
    "license": attr.string(
        doc = "A string specifying the license of the package.",
        default = "",
    ),
    "python_requires": attr.string(
        doc = (
            "Python versions required by this distribution, e.g. '>=3.5,<3.7'"
        ),
        default = "",
    ),
    "strip_path_prefixes": attr.string_list(
        default = [],
        doc = "path prefixes to strip from files added to the generated package",
    ),
}

sematic_py_wheel = rule(
    implementation = _sematic_py_wheel_impl,
    doc = """
A rule for building Python Wheels.
Wheels are Python distribution format defined in https://www.python.org/dev/peps/pep-0427/.
This rule packages a set of targets into a single wheel.
Currently only pure-python wheels are supported.
Examples:
```python
# Package some specific py_library targets, without their dependencies
py_wheel(
    name = "minimal_with_py_library",
    # Package data. We're building "example_minimal_library-0.0.1-py3-none-any.whl"
    distribution = "example_minimal_library",
    python_tag = "py3",
    version = "0.0.1",
    deps = [
        "//examples/wheel/lib:module_with_data",
        "//examples/wheel/lib:simple_module",
    ],
)
# Use py_package to collect all transitive dependencies of a target,
# selecting just the files within a specific python package.
py_package(
    name = "example_pkg",
    # Only include these Python packages.
    packages = ["examples.wheel"],
    deps = [":main"],
)
py_wheel(
    name = "minimal_with_py_package",
    # Package data. We're building "example_minimal_package-0.0.1-py3-none-any.whl"
    distribution = "example_minimal_package",
    python_tag = "py3",
    version = "0.0.1",
    deps = [":example_pkg"],
)
```
""",
    attrs = _concat_dicts(
        {
            "deps": attr.label_list(
                doc = """\
Targets to be included in the distribution.
The targets to package are usually `py_library` rules or filesets (for packaging data files).
Note it's usually better to package `py_library` targets and use
`entry_points` attribute to specify `console_scripts` than to package
`py_binary` rules. `py_binary` targets would wrap a executable script that
tries to locate `.runfiles` directory which is not packaged in the wheel.
""",
            ),
            "_wheelmaker": attr.label(
                executable = True,
                cfg = "exec",
                default = "@rules_python//tools:wheelmaker",
            ),
        },
        _distribution_attrs,
        _requirement_attrs,
        _entrypoint_attrs,
        _other_attrs,
    ),
)