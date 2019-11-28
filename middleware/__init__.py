import os
from pathlib import Path
from typing import List

import sqlalchemy
from flask import Flask
from flask_admin import Admin
from flask_cors import CORS
from flask_socketio import SocketIO
from loguru import logger
from rq import Connection, Queue

from . import models, routes, services
from .workers import REDIS_URL, redis_connection
from .workers.fingerprint_extractor import EXTRACT_QUEUE_NAME


cors = CORS()
admin = Admin(template_mode="bootstrap3")


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ['APP_SETTINGS'])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # TODO: Worth setting up this? See
    # https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xxii-background-jobs
    # app.redis = Redis.from_url(app.config['REDIS_URL'])
    # app.task_queue = rq.Queue('tasks', connection=app.redis)

    models.init_app(app)  # inits db
    admin.init_app(app)

    cors.init_app(app)

    routes.init_app(app)  # inits socketio
    services.init_app(app)

    @app.before_first_request
    def process_archive():  # type: ignore
        if app.config['TESTING']:
            return

        for file_path in get_archive_videos(Path(app.config['ARCHIVE_DIRECTORY'])):
            try:
                models.db.session.add(models.video_file.VideoFile(file_path))
                models.db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                logger.warning(f'{file_path.name} already in database, skipping...')
                logger.trace(e)

        reference_archive = models.db.session.query(models.video_file.VideoFile).all()

        with Connection(redis_connection):
            for archive_video in reference_archive:
                if archive_video.is_fingerprinted():
                    logger.trace(
                        f'{archive_video.video_name} already fingerprinted, skipping...'
                    )
                    pass

                logger.info(f'Computing fingerprints for {str(archive_video)}')

                q = Queue(EXTRACT_QUEUE_NAME)
                file_path = Path(archive_video.file_path)
                process_job = q.enqueue(services.files.process, file_path)
                q.enqueue(mark_as_done, file_path, depends_on=process_job)

    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": models.db}

    return app


# TODO: Replace by event
def mark_as_done(file_path: Path):
    video_file = (
        models.db.session.query(models.video_file.VideoFile)
        .filter_by(video_name=file_path.name)
        .first()
    )
    video_file.mark_as_fingerprinted()
    models.db.session.commit()

    SocketIO(message_queue=REDIS_URL).emit(
        'state_change',
        {'name': video_file.video_name, 'state': video_file.processing_state.name},
    )


def get_archive_videos(archive_video_directory: Path) -> List[Path]:
    assert archive_video_directory.exists()
    assert archive_video_directory.is_dir()

    all_paths_in_archive_video_directory = archive_video_directory.glob('**/*')
    archive_video_files = list(
        filter(Path.is_file, all_paths_in_archive_video_directory)
    )
    return archive_video_files
