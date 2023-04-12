<!--
When updating the version, update versions.py and wheel_constants.bzl accordingly.
Lines for version numbers should always be formatted as
`* [MAJOR.MINOR.PATCH](https://pypi.org/project/sematic/MAJOR.MINOR.PATCH/)`
with nothing else on the line.
-->
* HEAD
* [0.28.1](https://pypi.org/project/sematic/0.28.1/)
    * [improvement] Allow selecting S3 paths in UI
    * [improvement] Backend logging improvements
    * [bugfix] Ensure gevent import doesn't monkeypatch standard lib late when importing Sematic
    * [bugfix] Resolve issue with S3 links in the UI for S3 "directories"
    * [bugfix] Eliminate one situation that could lead to duplicated logs in the UI
    * [bugfix] Fix a casting issue with floats
* [0.28.0](https://pypi.org/project/sematic/0.28.0/)
    * [feature] Display metrics for pipelines (success rate, run count, runtime)
    * [feature] Added support for setting and memorizing a dev debug flag for the Dashboard
    * [deprecation] Deprecate Kubernetes 1.22 support
    * [improvement] Backend improvements to syncing with Kubernetes job states
    * [improvement] Several minor logging improvements and fixes
    * [bugfix] Enable local server to run with python 3.10
    * [bugfix] Ensured different users can rerun a pipeline
    * [bugfix] Ensured pipeline reruns use the submitting user's credentials
    * [bugfix] Ensure canceled/terminated runs have proper runtime display
    * [bugfix] Properly display duration for cloned runs
    * [bugfix] Fix matplotlib figure serialization, use Sematic Image type for support
    * [bugfix] Make storage object URL redirects consistent
    * [bugfix] Remove possible infinite reconnect loop when canceling local runs
    * [bugfix] Fixed a bug where the Resolver Socket.io client would not be cleanly closed
    * [bugfix] Fix corner case in the comparison of sqlite versions
    * [bugfix] Wrap long pipeline import paths in pipeline/run display
* [0.27.0](https://pypi.org/project/sematic/0.27.0/)
    * [feature] Added new S3Location and S3Bucket types that render S3 links in the Dashboard, and
      documented them
    * [feature] Added a new Image type that render images in the Dashboard, and documented it
    * [example] Added TorchLightning + Resnet + Ray example
    * [example] Added Ray AIR example
    * [example] Added various enhancements to the example Testing Pipeline
    * [improvement] BREAKING CHANGE: `image_layers` field in `sematic_pipeline` bazel macro
      now ONLY gets passed to image layering, and not also to the Sematic binary target.
      if you are using `image_layers` to express dependencies of a pipeline, you will now
      need to duplicate them in the `deps` field.
    * [improvement] Added support for Python 3.10
    * [improvement] Added support for Python 3.10-style type hints
    * [improvement] The Dashboard login flow will now redirect to the requested page instead of to
      the homepage
    * [improvement] Displaying the user who started a Run in the Dashboard Run list page and in the
      Run history drop-down
    * [improvement] Various documentation updates and fixes
    * [improvement] Various log message improvements and enhancements
    * [improvement] Sped up Docker image generation through various improvements
    * [improvement] Automatically update npm dependencies when building the wheel
    * [improvement] Added deep-linking selected panel stickiness in the Dashboard
    * [improvement] Filtered only pipelines launched by the current user in the Dashboard homepage
      last run widget
    * [improvement] Documented Ray integration architecture
    * [improvement] Improved wheel building portability by defaulting to bash
    * [improvement] Improved reaction time of the CloudResolver after a very long-running cloud Run
      has ended
    * [improvement] Improved handling of incorrect cleanup of or errors in subprocess spawned by
      user code
    * [improvement] Various internal refactorings, cleanups, and build improvements
    * [improvement] Switched from MB and GB to GiB and MiB in the Ray configurations, for
      consistency and standardization reasons
    * [improvement] Added checks and documentation for the new libmagic dependency
    * [improvement] Resolution failures caused by Resolver errors now get marked as failed instead
      of canceled
    * [bugfix] Pinned MNIST example pipeline dependencies after a new dependency release broke the
      execution
    * [bugfix] Fixed a bug that prevented the browser back/forward buttons from working correctly
      in the Dashboard
    * [bugfix] Fixed a bug that sometimes prevented the Dashboard Run tree panel from updating
    * [bugfix] Fixed sorting of the Runs in the Dashboard Run tree panel by creation time
    * [bugfix] Fixed a race condition where Kubernetes job updates would be incorrectly handled,
      and added safeguards for incorrect Run state transitions
    * [bugfix] Fixed a bug where killing a subprocess spawned by user code would prematurely
      terminate the Run, or leave the Resolver in an inconsistent state
    * [bugfix] Fixed a race condition that would prevent a fresh deployment on Kubernetes due to
      missing resources
    * [bugfix] Fixed a bug in the Dashboard that prevented the log panel error messages from
      refreshing when seeking to a different Run
    * [bugfix] Fixed a bug where failure to notify the Dashboard or Resolver with Run updates via
      socketio messages would cause the Resolution to fail
* [0.26.0](https://pypi.org/project/sematic/0.26.0/)
    * [feature] Added optional anonymized user analytics to track Sematic usage[^2]
    * [improvement] Atomic database migrations with Helm hooks
    * [improvement] Move future pickle storage to new server-generated locations
    * [improvement] Refactor in-app links to use react router
    * [improvement] Minor UI test improvements with Cypress
    * [improvement] Minor documentation fixes for rerun-from-here
    * [bugfix] Fix noop SQL migrations
* [0.25.0](https://pypi.org/project/sematic/0.25.0/)
    * [feature] New dashboard page showing a searchable list of runs
    * [feature] Enable links to runs using only the run id (pipeline path not required)
    * [improvement] Expose image layer caching configuration for bazel-built pipelines
    * [improvement] Make allocation timeouts for Ray clusters configurable
    * [improvement] Small changes to layout of pipeline display page
    * [improvement] Have Ray workers use same Kubernetes SA as Sematic workers
    * [improvement] Minor user docs improvements
    * [bugfix] Fix a bug that was preventing configuration of Slack via helm
    * [bugfix] Remove error occurring when a local settings file configures server-only settings
    * [bugfix] Be more resilient against non-standard failures during `torch` imports
    * [bugfix] More robust cleanup of Ray clusters on pipeline cancellation
* [0.24.1](https://pypi.org/project/sematic/0.24.1/)
    * [improvement] Show more detailed errors on failures of DB migrations
    * [bugfix] Reduce wheel size
* [0.24.0](https://pypi.org/project/sematic/0.24.0/)
    * [feature] Introduction of RayCluster[^1]
    * [feature] "Tee" cloud function logs so they appear in Sematic dashboard and the pod logs
    * [improvement] Visualize better which run was the true "root failure" when a resolution fails
    * [improvement] Improve an error message when using untyped dicts in type annotations
    * [improvement] Various improvements to Sematic internal test infrastructure
    * [bugfix] Remove a possible server crash for local servers running on Macs
    * [bugfix] Eliminate a bug that could leave runs hanging if multiple cancellation events were sent
    * [bugfix] Fix a bug that removed a useful default for image tag in the Helm chart
    * [bugfix] Rename an incorrectly named helm-chart value for Slack integration
    * [bugfix] Gracefully terminate runs when a resolver pod restarts mid-resolution
* [0.23.0](https://pypi.org/project/sematic/0.23.0/)
    * [feature] Ability to deploy socket.io micro-service separately.
    * [feature] Expose external resources in the dashboard.
    * [feature] Slack notification integration for failed resolutions.
    * [feature] Support the `debug` query parameter which can be added to any URL to enforce the front-end application to emit logs.
    * [improvement] Minor dependency and CI improvement.
    * [improvement] Minor development documentation improvements.
    * [bugfix] Fix a bug in the dashboard which prevents successful resolution of status update.
* [0.22.2](https://pypi.org/project/sematic/0.22.2/)
    * [feature] Add the ability to cache the output of a function and avoid its re-execution in
      the future
    * [feature] Add the ability to disable Sematic log ingestion for remote runs
    * [feature] Expose cloned run information in the dashboard
    * [improvement] Minor logging improvements
    * [improvement] Support configuring plugins from the CLI
    * [improvement] Add support for Bazel 6.0.0
    * [improvement] Add a link in output panel pointing to logs panel in case of error
    * [improvement] Improve robustness of data persistence
    * [improvement] Minor Helm documentation improvements
    * [improvement] Make the header sticky on the run details page
    * [improvement] Minor dashboard experience improvement
    * [improvement] Internal API endpoints expansion
    * [improvement] Support for non-deterministic cached builds in Bazel
    * [bugfix] Support override of settings even when no settings file exists
    * [bugfix] Minor cross version client support fixes
    * [bugfix] Make _getitem importable on graph cloning
* [0.22.1](https://pypi.org/project/sematic/0.22.1/)
    * [feature] Hide some "utility" autogenerated runs in the UI (ex: `_getitem`)
    * [improvement] Added functionality to some server APIs
    * [bugfix] To the script to allow auto-upgrading settings files.
      **IMPORTANT**: Users should run `sematic migrate` upon install
* [0.22.0](https://pypi.org/project/sematic/0.22.0/)
    * [feature] Expose in the dashboard when a run is cloned from another
    * [feature] Allow specifying multiple e-mail domains that can authenticate to Sematic
    * [feature] Deep linking for highlighting nested runs in the dashboard
    * [feature] Deep linking for tabs in the dashboard
    * [feature] Support clicking artifacts in the DAG view to get to their display page
    * [feature] Allow configuration for expanded shared memory on cloud workers
    * [feature] BREAKING CHANGE: Significant changes to our helm chart. Read our
      [deployment docs](https://docs.sematic.dev/diving-deeper/deploy) for more information.
    * [improvement] Improvements to logging UI performance
    * [improvement] Give an error message if there are futures that are not used for a
      function's final output
    * [improvement] Avoid warning about SQLite version when SQLite is not in use
    * [improvement] User-facing documentation revamp
    * [bugfix] Add `sematic.testing` to python wheel
    * [bugfix] Fix a bug with deserializing `Tuple` objects
    * [bugfix] Propagate tags and properties to cloned runs
    * [bugfix] Improve the behavior of the logging UI in case of errors
    * [bugfix] Better display of Union types in the dashboard
    * [bugfix] Add a missing requirement for one of the example pipelines
    * [bugfix] Prevent the dashboard from spamming the backend with requests
    * [bugfix] Fix corrupted settings files from 0.21.1
* [0.21.1](https://pypi.org/project/sematic/0.21.1/)
    * [bugfix] Add back feature allowing configuration of custom API URL to be used by workers
* [0.21.0](https://pypi.org/project/sematic/0.21.0/)
    * [feature] Add CLI for reading/following logs for a run
    * [feature] Enable configuration for the Kubernetes service account the workers will use
    * [improvement] Settings file schema changed to accomodate plug-in settings,
      files are migrated automatically.
    * [feature] Enable getting the id of the current run and root run from inside a Sematic func
    * [feature] Add custom display for Enum objects
    * [improvement] Settings file split between user settings `settings.yaml` and server settings `server.yaml`
    * [improvement] Make the run links in notes more obvious
    * [improvement] Fail early if attempting to retry an execution older than the server
      supports.
    * [bugfix] Fix a bug deserializing `Union` values. Note that once you are using this release,
      if you try to "rerun from here" using a pipeline that has `Union` values in it that were
      produced prior to this version of Sematic, the rerun will likely fail with a serialization issue.
    * [bugfix] BREAKING CHANGE: The examples' `README` files have been renamed to
      `README.md` in order for them to correctly render as MarkDown files. This change is
      required by the Bazel `example_pipeline` target as well
    * [bugfix] Missing broadcasts upon server-side run save
    * [bugfix] Cache version check
    * [bugfix] Fix a bug with loading logs with in-progress runs when you have reached the end
    * [bugfix] Fix a bug with displaying matplotlib figures in cloud deployments
* [0.20.1](https://pypi.org/project/sematic/0.20.1/)
    * [bugfix] Add support for subclasses of ABCMeta
* [0.20.0](https://pypi.org/project/sematic/0.20.0/)
    * [feature] Add datetime class and basic visualization
    * [feature] Support for switching between environment profiles
    * [feature] Add dynamic-shape testing pipeline
    * [improvement] Replace deprecated sklearn dependency with scikit-learn
    * [improvement] Support abstract base classes in type annotations
    * [improvement] Support automatic conversion of tuple-of-futures to future-tuple
    * [improvement] Change log-ingestion to use deltas rather than full files
    * [bugfix] Fix various DB migration script issues and add old sqlite3 version warning
    * [bugfix] Workaround for DB migration when Python installation comes with old sqlite3 version
    * [bugfix] Various minor build, execution, and code validation improvements and fixes
    * [bugfix] Add missing server permission to Helm chart
    * [bugfix] Fix various corner-case bugs which prevented re-running Resolutions
    * [bugfix] Fix launching example pipeline which require cli args
    * [bugfix] Fix rendering multi-line docstrings in the UI
    * [bugfix] Make server not start if the DB migration fails
* [0.19.2](https://pypi.org/project/sematic/0.19.2/)
    * [improvement] Various minor housekeeping improvements
    * [bugfix] Fix a bug in a DB migration script
* [0.19.1](https://pypi.org/project/sematic/0.19.1/)
    * [improvement] Various minor documentation improvements
    * [bugfix] Fix various bugs which prevented restarting resolutions from the UI
* [0.19.0](https://pypi.org/project/sematic/0.19.0/)
    * [feature] Expose Kubernetes infra failures in the Run panel
    * [feature] Enable restarting resolutions from the command line from a particular run, using different code
    * [feature] Enable restarting resolutions from the UI from a particular run
    * [feature] Support for easier testing of Sematic pipelines
    * [bugfix] Fix max parallelism for detached mode
* [0.18.1](https://pypi.org/project/sematic/0.18.1/)
    * [bugfix] Remove SQLAlchemy model dependencies from Python migrations
    * [bugfix] Enable usage of multiple base images in detached mode
* [0.18.0](https://pypi.org/project/sematic/0.18.0/)
    * [feature] Add ability to limit the number of parallel runs within a pipeline
    * [feature] Support for multiple bazel base container images
    * [enhancement] Ensure at one list element is displayed and increase max number displayed
    * [bugfix] Make sure retry works when parent exception class is specified
* [0.17.2](https://pypi.org/project/sematic/0.17.2/)
    * [bugfix] Correct fix GitInfo for custom Bazel workspaces
* [0.17.1](https://pypi.org/project/sematic/0.17.1/)
    * [feature] Add Sematic version cli command
    * [bugfix] Fix cancel button upon completion
    * [bugfix] Bump minimum client version to 0.17.0
    * [bugfix] Fix GitInfo for custom Bazel workspaces
* [0.17.0](https://pypi.org/project/sematic/0.17.0/)
    * [feature] Function Retry on failure
    * [feature] Expose pipeline git commit info in the UI
    * [feature] Cancel resolution support
* [0.16.0](https://pypi.org/project/sematic/0.16.0/)
    * [feature] Support Enums
    * [feature] Allow specifying Kubernetes tolerations for cloud jobs
    * [improvement] Redesigned log UI
* [0.15.1](https://pypi.org/project/sematic/0.15.1/)
    * [bugfix] Ensure log ingestion happens when using bazel cloud jobs and `dev=False`
    * [bugfix] Avoid spamming the server with requests for logs for incomplete runs
      without logs
* [0.15.0](https://pypi.org/project/sematic/0.15.0/)
    * [feature] Display logs for cloud jobs in the UI.
    * [improvement] Ensure the push of docker images by bazel works with docker
      credential helpers
* [0.14.0](https://pypi.org/project/sematic/0.14.0/)
    * [feature] BREAKING CHANGE: For cloud execution, users submitting pipelines no
      longer need Kubernetes access. Users who have deployed the Sematic server using
      docker will need to either (a) switch to deploying the server on Kubernetes or
      (b) use their Sematic deployment only for metadata tracking instead of metadata
      tracking + cloud execution.
    * [bugfix] Remove job environment variables from resolution API response
    * [improvement] Lower the probability of evictions of resolution jobs and improve
      handling of that situation
* [0.13.0](https://pypi.org/project/sematic/0.13.0/)
    * [bugfix] Bugfix for dicitonary visualization
    * [feature] When running in cloud mode, have the server log to stdout
    * [feature] Enable mounting Kubernetes secrets into the container
* [0.12.0](https://pypi.org/project/sematic/0.12.0/)
    * [feature] BREAKING CHANGE: Allow specifying resource requirements for Kubernetes
    jobs. `KubernetesResourceRequirements` has a new required field, `requests`
    * [feature] Add `has_container_image()` API for better control over launch workflows
    * [bugfix] Pass API key to request to fetch root run
* [0.11.0](https://pypi.org/project/sematic/0.11.0/)
    * [feature] Add a `get_artifact_value` API to retreive artifacts by ID
    * [feature] Add ability to link to individual runs on the UI, not just pipelines
    * [feature] Add option to serve local server from 0.0.0.0
    * [feature] Add capability to use different API URLs for local vs remote client usage
    * [feature] Enable environment variable to change Sematic config directory
    * [improvement] Add exceptions and other improved app logs to the server log files
    * [bugfix] Solve a bug with displaying empty lists in the UI
* [0.10.0](https://pypi.org/project/sematic/0.10.0/)
    * [improvement] Add support for python 3.8
    * [improvement] Friendly error message for unsupported Python version
    * [improvement] Friendly error message when clients don't match server version
* [0.9.0](https://pypi.org/project/sematic/0.9.0/)
    * [feature] Grafana integration for log panels
* [0.8.0](https://pypi.org/project/sematic/0.8.0/)
    * [feature] Capture exception stack traces and display in UI
* [0.7.0](https://pypi.org/project/sematic/0.7.0/)
    * [feature] Optional authentication with Google OAuth
* [0.6.0](https://pypi.org/project/sematic/0.6.0/)
    * [feature] Cloud execution with `CloudResolver`
    * [feature] Dependency packaging with the `sematic_pipeline` Bazel wheel
* [0.5.1](https://pypi.org/project/sematic/0.5.1/)
    * [bugfix] Fix JSON summary of Pandas dataframes with timestamp fields
* [0.5.0](https://pypi.org/project/sematic/0.5.0/)
    * [feature] `getitem` support for futures of list, tuples, dictionaries
    * [feature] `__iter__` support for futures of tuples
* [0.4.0](https://pypi.org/project/sematic/0.4.0/)
    * [feature] ability to deploy the Sematic API to a cloud instance and run
      pipelines against it (pipeline still runs locally)
    * [improvement] Rename `$ sematic credentials` to `$ sematic settings` to be
      able to store other things than credentials.
* [0.3.0](https://pypi.org/project/sematic/0.3.0/)
    * [feature] Support for Tuple types
    * [feature] Support for Dict types
    * [feature] `SnowflakeTable` type
    * [feature] `$ sematic credentials set <app> <var> <value>` CLI command
* [0.2.0](https://pypi.org/project/sematic/0.2.0/)
    * [bugfix] UI scroll issues
    * [bugfix] Dataframe UI previews fails for null/NaN values
    * [improvement] link to docs in exceptions for unsupported future operations
    * [example] dynamic graph examples
* [0.1.2-alpha](https://pypi.org/project/sematic/0.1.2a0/)
    * [bugfix] Fix example execution
* [0.1.1-alpha](https://pypi.org/project/sematic/0.1.1a0/)
    * [feature] Support for returning and passing lists of futures
    * [example] Dummy dynamic graph
    * [bugfix] List UI display
    * [improvement] Streamline examples, improve CLI experience
* [0.1.0-alpha](https://pypi.org/project/sematic/0.1.0a0/)
    * [feature] Show run panel when clicking run in DAG
    * [feature] When switching root run, stay on same function if possible
    * [feature] Discord link in side bar
    * [feature] Notes
    * [feature] `$ sematic new` CLI command
    * [bugfix] Style improvements to DAV view
* [0.0.4-alpha](https://pypi.org/project/sematic/0.0.4a0/)
    * New full-page app UI layout
* [0.0.3-alpha.2](https://pypi.org/project/sematic/0.0.3a2/)
    * [bugfix] Fix date display to cnvert from UTC
    * [bugfix] Fix migration bootstrapping to guarantee order of migrations
    * [feature] UI support for `pandas.DataFrame`
    * [feature] UI support for `matplotlib.figure.Figure`
    * [example] New liver cirrhosis prediction model (SKLearn, XGBoost)
* [0.0.2.alpha.1654828599](https://pypi.org/project/sematic/0.0.2a1654828599/)
    * Initial release

[^1]: This feature is for Sematic's "Enterprise Edition" only. Please reach out
to support@sematic.dev if you are interested in using Sematic EE.
[^2]: This release adds opt-out anonymized user analytics tracking to the Sematic
code.  You can opt-out of this tracking on the Sematic Dashboard home page.
