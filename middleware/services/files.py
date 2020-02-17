from ..models import db
from ..models.video_file import VideoFile, VideoFileSchema


SCHEMA = VideoFileSchema()


def list_files():
    video_files = db.session.query(VideoFile).all()

    return [SCHEMA.dump(v) for v in video_files]


def info(filename):
    db_video_file = db.session.query(VideoFile).filter_by(video_name=filename).first()
    return SCHEMA.dump(db_video_file)
