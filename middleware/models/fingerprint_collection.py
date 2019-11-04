import numpy as np
import base64

from video_reuse_detector.fingerprint import FingerprintCollection
from video_reuse_detector.color_correlation import ColorCorrelation

from . import db


class FingerprintCollectionModel(db.Model):  # type: ignore
    __tablename__ = 'fingerprints'

    pk = db.Column(db.Integer(), primary_key=True)

    # TODO: The keyframe serves no functional purpose
    # once the other fingerprints have been computed
    # and only has value from a debugging stand-point.
    # See commit "4251f77" for reference
    #
    # If kept, either base64 encode it as we do with
    # the thumbnail _or_ capture a path to the keyframe
    # from which we can load it whenever necessary.
    #
    # keyframe = sa.Column(sa.String())
    video_name = db.Column(db.String())
    segment_id = db.Column(db.Integer())
    thumbnail = db.Column(db.String())  # base64
    color_correlation = db.Column(db.BigInteger())
    orb = db.Column(db.ARRAY(db.Integer(), dimensions=2))

    def __init__(self,
                 video_name,
                 segment_id,
                 thumbnail,
                 color_correlation,
                 orb):
        self.video_name = video_name
        self.segment_id = segment_id
        self.thumbnail = thumbnail
        self.color_correlation = color_correlation
        self.orb = orb

    def __repr__(self):
        return '<pk {}>'.format(self.pk)

    def serialize(self):
        return {
            'pk': self.pk,
            'video_name': self.video_name,
            'segment_id': self.segment_id,
            'thumbnail': self.thumbnail,
            'color_correlation': self.color_correlation,
            'orb': self.orb,
        }

    def to_fingerprint_collection(self) -> FingerprintCollection:
        encoded = self.thumbnail
        decoded = base64.b64decode(encoded)
        thumbnail = np.frombuffer(decoded, dtype=np.uint8)

        # TODO: Thumbnails aren't guaranteed to be this size
        # right now. Expose class constant for defaults?
        thumbnail.resize((30, 30, 3))

        cc = ColorCorrelation.from_number(self.color_correlation)

        return FingerprintCollection(
            thumbnail,
            cc,
            np.array(self.orb, dtype=np.uint8),
            self.video_name,
            self.segment_id
        )

    @staticmethod
    def from_fingerprint_collection(fpc: FingerprintCollection):
        video_name = fpc.video_name
        segment_id = fpc.segment_id
        np_thumb = fpc.thumbnail.image
        encoded = base64.b64encode(np_thumb)
        color_correlation = fpc.color_correlation.as_number
        orb = None
        if fpc.orb is not None:
            orb = fpc.orb.descriptors.tolist()

        return FingerprintCollectionModel(
            video_name,
            segment_id,
            encoded,
            color_correlation,
            orb)
