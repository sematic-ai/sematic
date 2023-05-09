"""Augment or modify the returned json for ORM models for returns from API calls."""
# Standard Library
import logging
from typing import Any, Dict, List, Protocol, Sequence

# Sematic
from sematic.db.models.resolution import Resolution
from sematic.db.models.run import Run
from sematic.db.queries import get_user, get_users_by_id

logger = logging.getLogger(__name__)


class _JSONEncodableWithUser(Protocol):
    @property
    def user_id(self) -> str:
        ...

    def to_json_encodable(self) -> Dict[str, Any]:
        ...


def _get_payload_with_user(item: _JSONEncodableWithUser) -> Dict[str, Any]:
    item_payload = item.to_json_encodable()

    user_payload = None
    if item.user_id is not None:
        user = get_user(item.user_id)
        user_payload = user.to_json_encodable()

    item_payload["user"] = user_payload

    return item_payload


def _get_collection_payload_with_user(
    items: Sequence[_JSONEncodableWithUser],
) -> List[Dict[str, Any]]:
    items_payload = []

    user_ids = [item.user_id for item in items if item.user_id is not None]

    users_by_id = {}
    if len(user_ids) > 0:
        users_by_id = {
            user.id: user.to_json_encodable() for user in get_users_by_id(user_ids)
        }

    for item in items:
        item_payload = item.to_json_encodable()
        item_payload["user"] = None

        # this code is also used for the `notes` endpoint, which does not specify a run,
        # so the function_path path could be not set
        # but the `runs` endpoints needs calculator_path to be set for
        # backwards-compatibility
        if item_payload.get("function_path") is not None:
            item_payload["calculator_path"] = item_payload["function_path"]

        if item.user_id is not None:
            item_payload["user"] = users_by_id[item.user_id]

        items_payload.append(item_payload)

    return items_payload


# TODO: revert this change in 0.31.0
# get_run_payload = _get_payload_with_user
def get_run_payload(run: Run) -> Dict[str, Any]:
    payload = _get_payload_with_user(run)

    payload["calculator_path"] = payload["function_path"]

    return payload


get_runs_payload = _get_collection_payload_with_user


def get_resolution_payload(resolution: Resolution) -> Dict[str, Any]:
    payload = _get_payload_with_user(resolution)
    # Temporary to ensure backward compatibility for a few releases
    # https://github.com/sematic-ai/sematic/issues/612
    payload["settings_env_vars"] = {}
    return payload


get_note_payload = _get_payload_with_user
get_notes_payload = _get_collection_payload_with_user
