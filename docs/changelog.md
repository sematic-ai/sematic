<!--- When updating the version, update versions.py and sematic/BUILD accordingly -->
* HEAD
* 0.10.0
    * [improvement] Add support for python 3.8
    * [improvement] Friendly error message for unsupported Python version
    * [improvement] Friendly error message when clients don't match server version
* 0.9.0
    * [feature] Grafana integration for log panels
* 0.8.0
    * [feature] Capture exception stack traces and display in UI
* 0.7.0
    * [feature] Optional authentication with Google OAuth
* 0.6.0
    * [feature] Cloud execution with `CloudResolver`
    * [feature] Dependency packaging with the `sematic_pipeline` Bazel wheel
* 0.5.1
    * [bugfix] Fix JSON summary of Pandas dataframes with timestamp fields
* 0.5.0
    * [feature] `getitem` support for futures of list, tuples, dictionaries
    * [feature] `__iter__` support for futures of tuples
* 0.4.0
    * [feature] ability to deploy the Sematic API to a cloud instance and run
      pipelines against it (pipeline still runs locally)
    * [improvement] Rename `$ sematic credentials` to `$ sematic settings` to be
      able to store other things than credentials.
* 0.3.0
    * [feature] Support for Tuple types
    * [feature] Support for Dict types
    * [feature] `SnowflakeTable` type
    * [feature] `$ sematic credentials set <app> <var> <value>` CLI command
* 0.2.0
    * [bugfix] UI scroll issues
    * [bugfix] Dataframe UI previews fails for null/NaN values
    * [improvement] link to docs in exceptions for unsupported future operations
    * [example] dynamic graph examples
* 0.1.2-alpha
    * [bugfix] Fix example execution
* 0.1.1-alpha
    * [feature] Support for returning and passing lists of futures
    * [example] Dummy dynamic graph
    * [bugfix] List UI display
    * [improvement] Streamline examples, improve CLI experience
* 0.1.0-alpha
    * [feature] Show run panel when clicking run in DAG
    * [feature] When switching root run, stay on same function if possible
    * [feature] Discord link in side bar
    * [feature] Notes
    * [feature] `$ sematic new` CLI command
    * [bugfix] Style improvements to DAV view
* 0.0.4-alpha
    * New full-page app UI layout
* 0.0.3-alpha.2
    * [bugfix] Fix date display to cnvert from UTC
    * [bugfix] Fix migration bootstrapping to guarantee order of migrations
    * [feature] UI support for `pandas.DataFrame`
    * [feature] UI support for `matplotlib.figure.Figure`
    * [example] New liver cirrhosis prediction model (SKLearn, XGBoost)
* 0.0.2.alpha.1654828599
    * Initial release