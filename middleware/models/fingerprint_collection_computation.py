from . import db


class FingerprintCollectionComputation(db.Model):  # type: ignore
    __tablename__ = 'fingerprint_collection_computation'

    pk = db.Column(db.Integer(), primary_key=True)
    video_name = db.Column(db.String())
    video_duration = db.Column(db.Float())
    processing_time = db.Column(db.Float())
