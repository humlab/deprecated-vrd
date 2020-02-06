from pathlib import Path
from typing import List

import sqlalchemy
from flask import current_app
from flask.cli import FlaskGroup
from loguru import logger
from rq import Connection, Worker

from . import create_app
from .models import db
from .models.video_file import VideoFile


cli = FlaskGroup(create_app=create_app)


def get_videos_in_directory(video_directory: Path) -> List[Path]:
    assert video_directory.exists()
    assert video_directory.is_dir()

    all_paths_in_video_directory = video_directory.glob('**/*')
    video_files = list(filter(Path.is_file, all_paths_in_video_directory))

    return video_files


def insert_videos_from_directory(directory: Path, video_file_instantiator):
    for file_path in get_videos_in_directory(directory):
        try:
            db.session.add(video_file_instantiator(file_path))
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            logger.warning(f'{file_path.name} already in database, skipping...')
            db.session.rollback()
            logger.trace(e)


@cli.command('recreate_db')
def recreate_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command('run_extractor')
def run_extractor():
    with Connection(current_app.redis):
        worker = Worker(current_app.extract_queue)
        worker.work()


@cli.command('run_comparator')
def run_comparator():
    with Connection(current_app.redis):
        worker = Worker(current_app.compare_queue)
        worker.work()


@cli.command('seed_query_videos')
def seed_query_videos():
    uploads_directory = current_app.config['UPLOADS_DIRECTORY']
    assert uploads_directory.exists()

    logger.info(f'Seeding query videos from directory \"{uploads_directory}\"')

    insert_videos_from_directory(uploads_directory, VideoFile.from_upload)


@cli.command('seed_archive_videos')
def seed_archive_videos():
    archive_directory = current_app.config['ARCHIVE_DIRECTORY']
    assert archive_directory.exists()

    logger.info(f'Seeding reference videos from directory \"{archive_directory}\"')

    insert_videos_from_directory(archive_directory, VideoFile.from_archival_footage)


if __name__ == '__main__':
    cli()
