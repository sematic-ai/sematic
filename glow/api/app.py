# Third party
from flask import Flask
from flask_cors import CORS


glow_api = Flask(__name__, static_folder="../ui/build/static")

CORS(glow_api, resources={r"/api/*": {"origins": "*"}})
