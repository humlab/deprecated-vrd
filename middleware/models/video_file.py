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


class VideoFileType(Enum):
    QUERY = auto()
    REFERENCE = auto()

    @staticmethod
    def from_str(label: str):
        if label == 'QUERY':
            return VideoFileType.QUERY
        elif label == 'REFERENCE':
            return VideoFileType.REFERENCE
        else:
            expected_values = list(map(lambda ft: ft.name, VideoFileType))
            raise ValueError(
                f'Unexpected value for VideoFileType. Got={label}.'
                f' Expected={expected_values}'
            )


class VideoFileState(Enum):
    NOT_FINGERPRINTED = auto()
    FINGERPRINTED = auto()
    UPLOADED = auto()


class VideoFile(db.Model):  # type: ignore
    pk = db.Column(db.Integer(), primary_key=True)
    video_name = db.Column(db.String(), unique=True)
    # TODO: Add video_duration = db.Column(db.Float()) and
    # have computations have a FK to here
    file_path = db.Column(db.String())
    processing_state = db.Column(db.Enum(VideoFileState))
    file_type = db.Column(db.Enum(VideoFileType))

    def __init__(self, file_path: Path, file_type: VideoFileType):
        self.video_name = file_path.name
        self.file_path = str(file_path)
        self.processing_state = VideoFileState.NOT_FINGERPRINTED
        self.file_type = file_type

    def mark_as_fingerprinted(self):
        self.processing_state = VideoFileState.FINGERPRINTED

    def is_fingerprinted(self):
        return self.processing_state == VideoFileState.FINGERPRINTED

    @staticmethod
    def from_upload(file_path: Path) -> 'VideoFile':
        video_file = VideoFile(file_path, VideoFileType.QUERY)
        video_file.processing_state = VideoFileState.UPLOADED

        return video_file

    @staticmethod
    def from_archival_footage(file_path: Path) -> 'VideoFile':
        return VideoFile(file_path, VideoFileType.REFERENCE)

    def __repr__(self):
        return f'VideoFile={VideoFileSchema().dumps(self)}'

    def __commit_insert__(self):
        emit_event(self, 'video_file_added')

        file_path = self.file_path

        logger.debug(
            f'Extracting fingerprints for "{file_path}" after insertion of "{self}""'  # noqa: E501
        )

        extract_job = current_app.extract_queue.enqueue(extract_fingerprints, file_path)

        # Important to enqueue at front otherwise the UI is not notified until
        # the entire set of videos available at start-up has been processed.
        current_app.extract_queue.enqueue(
            mark_as_done, file_path, depends_on=extract_job, at_front=True
        )


def __mark_as_done__(file_path: Path):
    video_name = file_path.name
    logger.debug(f'Marking "{video_name}" as fingerprinted')
    video_file = db.session.query(VideoFile).filter_by(video_name=video_name).first()
    video_file.mark_as_fingerprinted()
    db.session.commit()
    emit_event(video_file, 'video_file_fingerprinted')


def mark_as_done(file_path: str):
    __mark_as_done__(Path(file_path))


def emit_event(video_file: VideoFile, event_name: str):
    logger.debug(f'Emitting "{event_name}" for {str(video_file)}')
    socketio.emit(event_name, VideoFileSchema().dump(video_file))


admin.add_view(ModelView(VideoFile, db.session))


class VideoFileSchema(ma.ModelSchema):
    processing_state = EnumField(VideoFileState)
    file_type = EnumField(VideoFileType)

    class Meta:
        model = VideoFile
