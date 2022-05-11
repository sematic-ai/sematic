# Third-party
from flask import jsonify

# Glow
from glow.api.app import glow_api
import glow.api.endpoints.runs  # noqa: F401


@glow_api.route("/")
def index():
    return jsonify({"hello": "world"})


@glow_api.route("/api/v1/ping")
def ping():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    glow_api.run(debug=True)
