from flask_admin.contrib.sqla import ModelView

from .. import admin
from . import db


class FingerprintComparisonComputation(db.Model):  # type: ignore
    __tablename__ = 'fingerprint_comparison_computation'

    pk = db.Column(db.Integer(), primary_key=True)
    query_video_name = db.Column(db.String())
    query_video_duration = db.Column(db.Float())

    reference_video_name = db.Column(db.String())
    reference_video_duration = db.Column(db.Float())

    processing_time = db.Column(db.Float())


admin.add_view(ModelView(FingerprintComparisonComputation, db.session))
