"""Augment or modify the returned json for ORM models for returns from API calls"""
# Standard Library
import logging
from typing import Any, Dict, List

# Sematic
from sematic.db.models.resolution import Resolution
from sematic.db.models.run import Run
from sematic.db.queries import get_users

logger = logging.getLogger(__name__)


def get_runs_payload(runs: List[Run]) -> List[Dict[str, Any]]:
    """
    Build the standard payload for a list of runs.
    """
    runs_payload = [run.to_json_encodable() for run in runs]

    _set_user_payloads(runs_payload)

    return runs_payload


def get_run_payload(run: Run) -> Dict[str, Any]:
    """
    Build the standard payload for a single run.
    """
    run_payload = run.to_json_encodable()

    _set_user_payloads([run_payload])

    return run_payload


def get_resolution_payload(resolution: Resolution) -> Dict[str, Any]:
    """
    Build the standard payload for a single resolution.
    """
    resolution_payload = resolution.to_json_encodable()
    # Setting this manual redaction for backward compatibility
    # ToDo: remove after a few releases
    resolution_payload["settings_env_vars"] = {}

    _set_user_payloads([resolution_payload])

    return resolution_payload


def _set_user_payloads(items: List[Dict[str, Any]]):
    """
    Sets item user payload.
    """
    try:
        user_ids = [item["user_id"] for item in items]
    except KeyError:
        raise ValueError(
            "'user_id' field was missing from one or more of the provided payloads"
        )

    users_by_id = {
        user.id: user.to_json_encodable(redact=True)
        for user in get_users(list(user_ids))
    }

    for item in items:
        item["user"] = users_by_id.get(item["user_id"])
