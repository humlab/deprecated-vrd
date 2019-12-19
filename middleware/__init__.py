import os

import rq
from flask import Flask
from flask_admin import Admin
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_sqlalchemy import models_committed
from redis import Redis

from . import models, routes, services


socketio = SocketIO()
cors = CORS()
admin = Admin(template_mode="bootstrap3")


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ['APP_SETTINGS'])

    # Necessary to support signalling
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

    # allows visiting of say, /admin, not requiring the trailing
    # slash, which is the default. I.e., by default, /admin/ is
    # required which is annoying
    app.url_map.strict_slashes = False

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.extract_queue = rq.Queue('extract', connection=app.redis)
    app.compare_queue = rq.Queue('compare', connection=app.redis)

    socketio.init_app(
        app, cors_allowed_origins="*", message_queue=app.config['REDIS_URL']
    )

    models.init_app(app)  # inits db
    models_committed.connect(on_models_committed, app)

    admin.init_app(app)

    cors.init_app(app)  # TODO: Required on blueprints as well?

    routes.init_app(app)
    services.init_app(app)

    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": models.db}

    return app


def on_models_committed(app, changes):
    for model, change in changes:
        if change == 'insert' and hasattr(model, '__commit_insert__'):
            model.__commit_insert__()
        if change == 'update' and hasattr(model, '__commit_update__'):
            model.__commit_update__()
        if change == 'delete' and hasattr(model, '__commit_delete__'):
            model.__commit_delete__()
