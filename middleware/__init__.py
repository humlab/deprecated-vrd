import os
from pathlib import Path
from typing import List

import rq
import sqlalchemy
from flask import Flask
from flask_admin import Admin
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_sqlalchemy import models_committed
from loguru import logger
from redis import Redis

from . import models, routes, services


socketio = SocketIO()
cors = CORS()
admin = Admin(template_mode="bootstrap3")


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ['APP_SETTINGS'])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.extract_queue = rq.Queue('extract', connection=app.redis)
    app.compare_queue = rq.Queue('compare', connection=app.redis)

    socketio.init_app(
        app, cors_allowed_origins="*", message_queue=app.config['REDIS_URL']
    )
    models.init_app(app)  # inits db
    models_committed.connect(on_models_committed, app)
    admin.init_app(app)

    cors.init_app(app)

    routes.init_app(app)  # inits socketio
    services.init_app(app)

    @app.before_first_request
    def process_archive():  # type: ignore
        if app.config['TESTING']:
            return

        insert_videos_from_directory(Path(app.config['ARCHIVE_DIRECTORY']))

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


def get_videos_in_directory(video_directory: Path) -> List[Path]:
    assert video_directory.exists()
    assert video_directory.is_dir()

    all_paths_in_video_directory = video_directory.glob('**/*')
    video_files = list(filter(Path.is_file, all_paths_in_video_directory))

    return video_files


def insert_videos_from_directory(directory: Path):
    for file_path in get_videos_in_directory(directory):
        try:
            models.db.session.add(models.video_file.VideoFile(file_path))
            models.db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            logger.warning(f'{file_path.name} already in database, skipping...')
            logger.trace(e)
