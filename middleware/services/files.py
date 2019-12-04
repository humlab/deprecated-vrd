from ..models import db
from ..models.video_file import VideoFile, VideoFileSchema


def list_files():
    video_files = db.session.query(VideoFile).all()

    return [VideoFileSchema().dump(v) for v in video_files]
