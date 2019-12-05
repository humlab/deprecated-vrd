from flask_admin.contrib.sqla import ModelView
from flask_socketio import SocketIO

from .. import admin
from ..config import Config
from . import db


socketio = SocketIO(message_queue=Config.REDIS_URL)


class FingerprintComparisonComputation(db.Model):  # type: ignore
    __tablename__ = 'fingerprint_comparison_computation'

    pk = db.Column(db.Integer(), primary_key=True)
    query_video_name = db.Column(db.String())
    query_video_duration = db.Column(db.Float())

    reference_video_name = db.Column(db.String())
    reference_video_duration = db.Column(db.Float())

    processing_time = db.Column(db.Float())

    def __commit_insert__(self):
        socketio.emit(
            'comparison_computation_completed',
            {
                'query_video_name': self.query_video_name,
                'reference_video_name': self.reference_video_name,
            },
        )


admin.add_view(ModelView(FingerprintComparisonComputation, db.session))
