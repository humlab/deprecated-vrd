import base64

import numpy as np
from loguru import logger

from video_reuse_detector.color_correlation import ColorCorrelation
from video_reuse_detector.fingerprint import FingerprintCollection
from video_reuse_detector.orb import ORB
from video_reuse_detector.thumbnail import Thumbnail

from . import db


class FingerprintCollectionModel(db.Model):  # type: ignore
    __tablename__ = 'fingerprint_collections'

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
    # It could be argued that a corollary of this is
    # that it would have value maintaining a reference
    # to the content which was fingerprinted, for an
    # example a URI, so that if the fingerprinting
    # process is altered in the future it'd be
    # possible to recompute fingerprints for previous
    # inputs.
    #
    # keyframe = db.Column(sa.String())
    video_name = db.Column(db.String())
    segment_id = db.Column(db.Integer())
    thumbnail = db.Column(db.LargeBinary())  # base64
    color_correlation = db.Column(db.BigInteger())
    orb = db.Column(db.ARRAY(db.Integer(), dimensions=2))

    def __init__(self, video_name, segment_id, thumbnail, color_correlation, orb):
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
        thumbnail = self.thumbnail  # encoded base64 string
        decoded = None

        try:
            decoded = base64.b64decode(thumbnail)
        except Exception as e:
            err_msg = (
                f'Could not decode thumbnail for video_name={self.video_name}'
                f' segment_id={self.segment_id}'
                f' length of encoding={len(thumbnail)}'
            )

            logger.error(err_msg)

            raise e

        thumbnail = np.frombuffer(decoded, dtype=np.float64)

        # TODO: Thumbnails aren't guaranteed to be this size
        # right now. Expose class constant for defaults?
        thumbnail = np.resize(thumbnail, (30, 30))

        cc = ColorCorrelation.from_number(self.color_correlation)

        orb = ORB(np.array(self.orb, dtype=np.uint8).tolist()) if self.orb else None

        return FingerprintCollection(
            Thumbnail(thumbnail), cc, orb, self.video_name, self.segment_id,
        )

    @staticmethod
    def from_fingerprint_collection(fpc: FingerprintCollection):
        video_name = fpc.video_name
        segment_id = fpc.segment_id
        np_thumb = fpc.thumbnail.image

        assert np_thumb.dtype == np.float64  # important!
        assert np_thumb.shape == (30, 30)

        encoded = base64.b64encode(np_thumb)
        color_correlation = fpc.color_correlation.as_number

        orb = None
        if fpc.orb is not None:
            orb = fpc.orb.descriptors.tolist()

        return FingerprintCollectionModel(
            video_name, segment_id, encoded, color_correlation, orb
        )
