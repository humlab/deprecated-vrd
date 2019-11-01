import os

from flask import Flask
from flask_cors import CORS


def create_app():
    from . import models, routes, services

    app = Flask(__name__)
    app.config.from_object(os.environ['APP_SETTINGS'])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    CORS(app)

    models.init_app(app)
    routes.init_app(app)
    services.init_app(app)

    return app
