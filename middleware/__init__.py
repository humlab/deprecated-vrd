import os

from flask import Flask
from flask_cors import CORS

cors = CORS()


def create_app():
    from . import models, routes, services

    app = Flask(__name__)
    app.config.from_object(os.environ['APP_SETTINGS'])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    models.init_app(app)  # inits db
    cors.init_app(app)

    routes.init_app(app)  # inits socketio
    services.init_app(app)

    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": models.db}

    return app