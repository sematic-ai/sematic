# Standard library
import enum
import os
from typing import Dict, Optional

# Third-arty
import yaml

# Sematic
from sematic.config import get_config


Credentials = Dict[str, Dict[str, str]]


def _load_credentials():
    with open(get_config().credentials_file, "r") as f:
        credentials = yaml.load(f, yaml.Loader)

    if credentials is None:
        return {}

    selected_credentials = credentials["default"]

    # Override with env vars
    for key, creds in selected_credentials.items():
        for var, value in creds.items():
            selected_credentials[key][var] = os.environ.get(var, value)

    return selected_credentials


_credentials: Optional[Credentials] = None


def get_credentials() -> Credentials:
    """
    Main API to access stored credentials.
    """
    global _credentials

    if _credentials is None:
        _credentials = _load_credentials()

    return _credentials


class CredentialKeys(enum.Enum):
    snowflake = "snowflake"


class MissingCredentialsError(Exception):
    pass


def get_credential(key: CredentialKeys, var: str) -> str:
    """
    Main API to access individual credential.
    """
    if key not in CredentialKeys.__members__.values():
        raise ValueError(
            "Invalid credentials key: {}. Available keys: {}".format(
                repr(key), CredentialKeys.__members__.values()
            )
        )

    credential = get_credentials().get(key.value, {}).get(var)

    if credential is None:
        raise MissingCredentialsError("Missing credentials: {}".format(var))

    return credential


def set_credential(key: CredentialKeys, var: str, value: str):
    if key not in CredentialKeys.__members__.values():
        raise ValueError(
            "Invalid credentials key: {}. Available keys: {}".format(
                repr(key), CredentialKeys.__members__.values()
            )
        )

    with open(get_config().credentials_file, "r") as f:
        credentials = yaml.load(f, yaml.Loader)

    if credentials is None:
        credentials = {"default": {}}

    credentials["default"][key.value][var] = value
    yaml_output = yaml.dump(credentials, Dumper=yaml.Dumper)

    with open(get_config().credentials_file, "w") as f:
        f.write(yaml_output)
