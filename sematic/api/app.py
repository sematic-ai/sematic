# Third party
from flask import Flask
from flask_cors import CORS


sematic_api = Flask(__name__, static_folder="../ui/build/static")

CORS(sematic_api, resources={r"/api/*": {"origins": "*"}})
