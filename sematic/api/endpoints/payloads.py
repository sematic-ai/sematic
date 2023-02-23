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

    _set_user_payloads([resolution_payload])

    return resolution_payload


def get_resolutions_payload(resolutions: List[Run]) -> List[Dict[str, Any]]:
    """
    Build the standard payload for a list of resolutions.
    """
    resolutions_payload = [resolution.to_json_encodable() for resolution in resolutions]

    _set_user_payloads(resolutions_payload)

    return resolutions_payload


def _set_user_payloads(items: List[Dict[str, Any]]):
    try:
        user_ids = [item["user_id"] for item in items]
    except KeyError as e:
        logger.error("Items are not payloads of owned models.")
        raise e

    users_by_id = {
        user.id: user.to_json_encodable() for user in get_users(list(user_ids))
    }

    for item in items:
        item["user"] = users_by_id.get(item["user_id"])
