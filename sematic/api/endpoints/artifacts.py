# Standard Library
from http import HTTPStatus
from typing import List, Optional

# Third-party
import flask
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import (
    get_request_parameters,
    jsonify_error,
)
from sematic.db.db import db
from sematic.db.models.artifact import Artifact
from sematic.db.models.user import User
from sematic.db.queries import get_artifact
from sematic.storage import StorageSettingValue, STORAGE_ENGINE_REGISTRY, StorageMode
from sematic.user_settings import get_user_settings, SettingsVar


@sematic_api.route("/api/v1/artifacts", methods=["GET"])
@authenticate
def list_artifacts_endpoint(user: Optional[User] = None) -> flask.Response:
    limit, _, _, sql_predicates = get_request_parameters(flask.request.args, Artifact)

    with db().get_session() as session:
        query = session.query(Artifact)

        if sql_predicates is not None:
            query = query.filter(sql_predicates)

        query = query.order_by(sqlalchemy.desc(Artifact.created_at))

        artifacts: List[Artifact] = query.limit(limit).all()

    payload = dict(content=[artifacts.to_json_encodable() for artifacts in artifacts])

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/artifacts/<artifact_id>/location/<mode>", methods=["GET"])
@authenticate
def get_artifact_location(
    user: Optional[User], artifact_id: str, mode: str
) -> flask.Response:
    try:
        storage_mode = StorageMode[mode.upper()]
    except KeyError:
        return jsonify_error(
            f"mode should be on of {[m.value for m in StorageMode]}, got {mode}",
            HTTPStatus.BAD_REQUEST,
        )

    storage_setting_value = get_user_settings(
        SettingsVar.SEMATIC_STORAGE, StorageSettingValue.LOCAL.value
    )

    try:
        storage_engine_class = STORAGE_ENGINE_REGISTRY[
            StorageSettingValue[storage_setting_value]
        ]
    except KeyError:
        return jsonify_error(
            f"Unknown storage engine: {storage_setting_value}",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    location = storage_engine_class().get_location(
        namespace="artifacts", key=artifact_id, mode=storage_mode
    )

    payload = dict(storage_engine=storage_setting_value, location=location)

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/artifacts/<artifact_id>", methods=["GET"])
@authenticate
def get_artifact_endpoint(user: Optional[User], artifact_id: str) -> flask.Response:
    """
    Retrive an artifact.

    Parameters
    ----------
    artifact_id: str
        ID of artifact to retrieve

    Returns
    -------
    content: Artifact
        The requested artifact in JSON format
    """
    try:
        artifact = get_artifact(artifact_id)
    except NoResultFound:
        return jsonify_error(
            "No Artifact with id {}".format(repr(artifact_id)), HTTPStatus.NOT_FOUND
        )

    payload = dict(
        content=artifact.to_json_encodable(),
    )

    return flask.jsonify(payload)
