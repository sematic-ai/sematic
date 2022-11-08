# Sematic
from sematic import client


def test_client():
    try:
        # validate that this function is imported and exposed in the module
        client.get_artifact_value  # type: ignore
    except AttributeError as e:
        assert False, str(e)
