# Bazel Tips

You can execute most things in this repo with bazel. Here are some particularly useful examples:

## Testing

This will execute all tests, including all supported versions of python.
```
bazel test //sematic/...
```

This will run a specific test (in this case the API client test), on the default python version.
The target path is the file path to to the python package where the test lives (`sematic.tests`
in the example below), followed by a colon and the name of the python module for the test
(`test_api_client` in this example).
```
bazel run //sematic/tests:test_api_client
```

This will run a specific test (in this case the API client test), on the python version indicated
by the `_py3X` (python 3.9 in the example below).
```
bazel run //sematic/tests:test_api_client_py39
```

If you are using VSCode, you can use the VSCode debugger with bazel while testing. First, you
need to add this to your VSCode `launch.json` configurations:
```
        {
            "name": "Python: Attach",
            "type": "python",
            "request": "attach",
            "port": 5724,
            "host": "localhost",
            "pathMappings": [
                {
                  "localRoot": "${workspaceFolder}",
                  "remoteRoot": "."
                }
            ]
        },
```

Once you've done that, you can debug tests with bazel by:
- Running your test with `DEBUGPY=1`: `DEBUGPY=1 bazel run //sematic/tests:test_api_client`
- once the test has paused (should pause very quickly), execute the `Python: Attach` debug
configuration from your VSCode debug panel. It should attach to the debugger.
- While the debugger is running, you can use all the debugger features you'd expect: breakpoints,
stepping, variables and watch views, stack navigation, etc..


## IPython
You can open an iPython shell that contains the dependencies for any `sematic_py_lib`:
```
$ bazel run //sematic:api_client_ipython  # build //sematic:api_client and open a shell
In [1]: from sematic import api_client as api
```

You can also do this for specific versions of python by adding a `_py3X_` between the
name of the lib target and the `ipython`:
```
$ bazel run //sematic:api_client_py39_ipython  # build target and open a py3.9 shell
In [1]: from sematic import api_client as api
```

## Sematic examples
You can run Sematic examples by running one of the targets created with the
`sematic_example` build macro:
```
$ bazel run //sematic/examples/liver_cirrhosis:liver_cirrhosis
```

You can do this using a specific interpreter as well with a `_py3X` suffix:
```
$ bazel run //sematic/examples/liver_cirrhosis:liver_cirrhosis_py39
```

You can also open an ipython interpreter into the environment for the example:
```
$ bazel run //sematic/examples/liver_cirrhosis:liver_cirrhosis_py39_ipython
In [1]: from sematic.examples.liver_cirrhosis import *
```

## Sematic CLI
For the sematic CLI (as well as any other `sematic_py_binary`), you can run them
by just running their targets:

```
$ bazel run //sematic/cli:main -- --help
```

You can also do *this* with specific python interpreters:
```
$ bazel run //sematic/cli:main_py39 -- --help
```