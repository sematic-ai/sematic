# Sematic
from sematic.plugins.building import docker_client_utils


def test_docker_status_update_to_str():
    actual_str = docker_client_utils._docker_status_update_to_str({})
    assert actual_str is None

    actual_str = docker_client_utils._docker_status_update_to_str({"k1": " ", "k2": ""})
    assert actual_str is None

    actual_str = docker_client_utils._docker_status_update_to_str({"k1": " v1 "})
    assert actual_str == "v1"

    actual_str = docker_client_utils._docker_status_update_to_str(
        {"k1": " v1 ", "k2": ""}
    )
    assert actual_str == "v1"

    actual_str = docker_client_utils._docker_status_update_to_str(
        {"k3": " v3 ", "k2": "", "k1": {"a": 1}}
    )
    assert actual_str == "{'a': 1} v3"
