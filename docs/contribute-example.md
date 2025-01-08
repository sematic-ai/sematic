## Contribute an example pipeline

Example pipelines are stored at
[sematic/examples](https://github.com/sematic-ai/sematic/tree/main/sematic/examples).

Select examples are included in Sematic's Python pip wheel and accessible to
every user out-of-the-box.

Examples have two main goals:

* Showcasing the extent of Sematic's capability: different use cases, different
  integrations with third-party services, visualizations, etc.
* Promoting good practices and patterns to write pipelines.

Here's how to get started implementing your own example.

### Implement a pipeline

First follow the steps in [Your first pipeline](./first-pipeline.md) or [A real
ML pipeline](./real-example.md) to create a working example pipeline.


### Integrate it into the codebase

When you are ready to integrate it into the codebase, do:

```shell
$ git clone https://github.com/sematic-ai/sematic.git
```

Then create a branch for your example:

```shell
$ cd sematic
$ git checkout -b <your-github-username>/<your-example-name>
```

Then copy your example's package in the example directory

```shell
$ cp -rf path/to/my_package sematic/examples/
```

In Sematic, we use absolute import paths everywhere. So you need to prefix all
your local imports with `sematic.examples`.

Change

```python
from my_package.pipeline import pipeline
```

to

```python
from sematic.examples.my_package.pipeline import pipeline
```

### Third-party requirements

Sematic keeps a centralized list of third-party requirements in its pyproject.toml

If the third-party libraries required by your new examples are not in there
, add them under the `examples` optional dependencies.

Don't worry, your third-party dependencies will not be added to the Sematic pip wheel.

Finally, your package should contain a `requirements.txt` file. This is used to help users install the particular dependencies for your example (since they are not included in the main Sematic wheel).

### Document and credit yourself

Make sure all your Sematic Functions have good docstrings. You can use Markdown
to add links to external docs.

Add a `README` file at the root of your package with some baseline documentation.

Add your personal info to an `AUTHORS` file. You can add whatever you want
(email, Twitter, GitHub profile, etc.). This will be displayed to users when they run your example.


### Create a Pull Request

Push your branch:

```shell
$ git push origin your-branch-name
```

Then head over to [Sematic's Pull
Requests](https://github.com/sematic-ai/sematic/compare) to create one.

To increase your chances of being merged fast:

* Add a comprehensive description to your PR.
* Ensure your code is properly formatted and type checked.
  * Make sure you have the dev tools installed by running `make install-dev-deps` (you only ever need to do this once).
  * Use `make pre-commit` to run the linter and code formatter.
  * Use `make update-schema` to make sure any DB changes you made are accounted for.
* Make sure the CircleCI build passes for your branch (linked in the checks section at the bottom of the GitHub PR page).
* Add `sematic-ai/staff` as a reviewer, but also try to assign a specific reviewer, such as `neutralino1`.
