from flask_admin.contrib.sqla import ModelView

from .. import admin
from . import db


class FingerprintCollectionComputation(db.Model):  # type: ignore
    __tablename__ = 'fingerprint_collection_computation'

    pk = db.Column(db.Integer(), primary_key=True)
    video_name = db.Column(db.String())
    video_duration = db.Column(db.Float())
    processing_time = db.Column(db.Float())


class FingerprintCollectionComputationView(ModelView):
    can_export = True


admin.add_view(
    FingerprintCollectionComputationView(FingerprintCollectionComputation, db.session)
)
