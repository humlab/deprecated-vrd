from enum import Enum, auto
from pathlib import Path

from flask_admin.contrib.sqla import ModelView
from marshmallow_enum import EnumField

from .. import admin
from . import db, ma


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
        # TODO: Do we need to evaluate the unique constraint manually?
        self.video_name = file_path.name
        self.file_path = str(file_path)
        self.processing_state = VideoFileState.NOT_FINGERPRINTED

    def mark_as_fingerprinted(self):
        self.processing_state = VideoFileState.FINGERPRINTED

    def is_fingerprinted(self):
        return self.processing_state == VideoFileState.FINGERPRINTED

    def __repr__(self):
        return VideoFileSchema().dumps(self)


admin.add_view(ModelView(VideoFile, db.session))


class VideoFileSchema(ma.ModelSchema):
    processing_state = EnumField(VideoFileState)

    class Meta:
        model = VideoFile
