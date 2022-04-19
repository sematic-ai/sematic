# Developer manual

## Add third-party pip dependency

Add dependency to `requirements/requirements.in`, and if possible, set a fixed version.

Then run:
```shell
$ python3 -m piptools compile requirements/requirements.in > requirements/requirements.txt
```