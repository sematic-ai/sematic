# Standard Library
import hashlib
import json
from typing import Any

# Sematic
from sematic.utils.json import fix_nan_inf


def get_str_sha1_digest(string: str) -> str:
    """
    Get SHA1 hex digest for a string.
    """
    # we don't need a cryptographic hash, but we do need a fast hash
    # unfortunately the builtin hash is initialized with a random salt seed on program
    # initialization, and this cannot be reset,
    # so we use sha1 for now
    # https://automationrhapsody.com/md5-sha-1-sha-256-sha-512-speed-performance/
    binary = string.encode("utf-8")
    sha1_digest = hashlib.sha1(binary)

    return sha1_digest.hexdigest()


def get_value_and_type_sha1_digest(
    value_serialization: Any,
    type_serialization: Any,
    json_summary: Any,
) -> str:
    """
    Get SHA1 digest for a value and its type.
    """
    # TODO #403: do this in a sustainable and efficient way
    payload = {
        "value": value_serialization,
        "type": type_serialization,
        "summary": json_summary,
        # TODO: Should there be some sort of type versioning concept here?
    }

    string_payload = fix_nan_inf(json.dumps(payload, sort_keys=True, default=str))
    return get_str_sha1_digest(string_payload)
