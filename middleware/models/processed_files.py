from . import db


class ProcessedFileModel(db.Model):  # type: ignore
    __tablename__ = 'processed_files'

    pk = db.Column(db.Integer(), primary_key=True)

    video_name = db.Column(db.String())
