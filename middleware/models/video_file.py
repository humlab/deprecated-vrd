from enum import Enum, auto
from pathlib import Path

from flask import current_app
from flask_admin.contrib.sqla import ModelView
from flask_socketio import SocketIO
from loguru import logger
from marshmallow_enum import EnumField

from .. import admin
from ..config import Config
from ..services.fingerprint import extract_fingerprints
from . import db, ma


socketio = SocketIO(message_queue=Config.REDIS_URL)


class VideoFileState(Enum):
    NOT_FINGERPRINTED = auto()
    FINGERPRINTED = auto()


class VideoFile(db.Model):  # type: ignore
    pk = db.Column(db.Integer(), primary_key=True)
    video_name = db.Column(db.String(), unique=True)
    # TODO: Add video_duration = db.Column(db.Float()) and
    # have computations have a FK to here
    file_path = db.Column(db.String())
    processing_state = db.Column(db.Enum(VideoFileState))

    def __init__(self, file_path: Path):
        self.video_name = file_path.name
        self.file_path = str(file_path)
        self.processing_state = VideoFileState.NOT_FINGERPRINTED

    def mark_as_fingerprinted(self):
        self.processing_state = VideoFileState.FINGERPRINTED

    def is_fingerprinted(self):
        return self.processing_state == VideoFileState.FINGERPRINTED

    def __repr__(self):
        return VideoFileSchema().dumps(self)

    def __commit_insert__(self):
        file_path = self.file_path
        logger.debug(
            f'Extracting fingerprints for "{file_path}" after insertion of "VideoFile={self}""'  # noqa: E501
        )
        extract_job = current_app.extract_queue.enqueue(extract_fingerprints, file_path)
        current_app.extract_queue.enqueue(
            mark_as_done, file_path, depends_on=extract_job
        )

    def __commit_update__(self):
        logger.debug(f'"{self.video_name}" updated. Emitting "state_change"')
        socketio.emit(
            'state_change',
            {'name': self.video_name, 'state': self.processing_state.name},
        )


def __mark_as_done__(file_path: Path):
    video_name = file_path.name
    logger.info(f'Marking "{video_name}" as fingerprinted')
    video_file = db.session.query(VideoFile).filter_by(video_name=video_name).first()
    video_file.mark_as_fingerprinted()
    db.session.commit()


def mark_as_done(file_path: str):
    __mark_as_done__(Path(file_path))


admin.add_view(ModelView(VideoFile, db.session))


class VideoFileSchema(ma.ModelSchema):
    processing_state = EnumField(VideoFileState)

    class Meta:
        model = VideoFile
