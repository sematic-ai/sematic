# Standard Library
from http import HTTPStatus
from typing import Dict, List, Optional, Type, cast

# Third-party
import flask
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.abstract_plugin import PluginScope
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import (
    get_request_parameters,
    jsonify_error,
)
from sematic.config.settings import get_active_plugins
from sematic.db.db import db
from sematic.db.models.artifact import Artifact
from sematic.db.models.user import User
from sematic.db.queries import get_artifact, get_cached_artifact_and_run
from sematic.plugins.abstract_storage import AbstractStorage, PayloadType
from sematic.plugins.storage.local_storage import LocalStorage

CACHE_KEY = "cache_key"


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


@sematic_api.route("/api/v1/artifacts/<artifact_id>", methods=["GET"])
@authenticate
def get_artifact_endpoint(user: Optional[User], artifact_id: str) -> flask.Response:
    """
    Retrieve an artifact by its ID.

    Parameters
    ----------
    artifact_id: str
        ID of artifact to retrieve

    Response
    --------
    content: Artifact
        The requested artifact in JSON format
    """
    try:
        artifact = get_artifact(artifact_id)
    except NoResultFound:
        return jsonify_error(
            "No Artifact with id {}".format(repr(artifact_id)), HTTPStatus.NOT_FOUND
        )

    payload = dict(content=artifact.to_json_encodable())

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/artifacts/cache", methods=["GET"])
@authenticate
def get_cached_artifact_endpoint(user: Optional[User]) -> flask.Response:
    """
    Retrieve an Artifact from the cache, along with the Run that originally produced it.

    Request
    -------
    cache_key: str
        The cache key under which to look for the Artifact.

    Response
    --------
    artifact: Artifact
        The found Artifact in JSON format.
    run: Run
        The Run that originally produced the Artifact, in JSON format.
    """
    if CACHE_KEY not in set(flask.request.args.keys()):
        return jsonify_error(
            f"Can only get artifacts using the query key {CACHE_KEY}",
            HTTPStatus.BAD_REQUEST,
        )

    if len(flask.request.args.keys()) > 1:
        unknown_keys = set(flask.request.args.keys()) - {CACHE_KEY}
        return jsonify_error(
            f"Unknown query keys: {unknown_keys}", HTTPStatus.BAD_REQUEST
        )

    cache_key = flask.request.args[CACHE_KEY]
    payload: Dict[str, Optional[Dict[str, str]]] = dict(content=None)

    artifact_and_run = get_cached_artifact_and_run(cache_key)

    if artifact_and_run is None:
        # not finding an artifact is part of the normal flow and not an error case
        return flask.jsonify(payload)

    artifact, run = artifact_and_run
    payload["content"] = {
        "artifact": artifact.to_json_encodable(),
        "run": run.to_json_encodable(),
    }

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/artifacts/<artifact_id>/location", methods=["GET"])
@authenticate
def get_artifact_location_endpoint(user: Optional[User], artifact_id: str):
    # TODO: Validate that user has permission to access artifact
    try:
        storage_class = _get_storage_plugin()
    except NoActivePluginError:
        return jsonify_error(
            "Incorrect storage plugin scope", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    location = storage_class().get_write_location("artifacts", artifact_id)

    return flask.jsonify(dict(location=location))


@sematic_api.route("/api/v1/artifacts/<artifact_id>/data", methods=["GET"])
@authenticate
def get_artifact_data_endpoint(user: Optional[User], artifact_id: str):
    # TODO: Validate that user has permission to access artifact
    try:
        storage_class = _get_storage_plugin()
    except NoActivePluginError:
        return jsonify_error(
            "Incorrect storage plugin scope", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    read_payload = storage_class().get_read_payload("artifacts", artifact_id)

    if read_payload.type_ is PayloadType.URL:
        return flask.redirect(read_payload.content, code=HTTPStatus.FOUND)

    return flask.Response(read_payload.content)


class NoActivePluginError(Exception):
    pass


def _get_storage_plugin() -> Type[AbstractStorage]:
    try:
        storage_plugin = get_active_plugins(
            PluginScope.STORAGE, default=[LocalStorage]
        )[0]
    except IndexError:
        raise NoActivePluginError()

    storage_class = cast(Type[AbstractStorage], storage_plugin)

    return storage_class
