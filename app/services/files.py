from loguru import logger
from pathlib import Path

from ..models.base import db
from ..models.fingerprint_collection import FingerprintCollectionModel

from video_reuse_detector.segment import segment
from video_reuse_detector.downsample import downsample
from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.fingerprint import FingerprintCollection
import video_reuse_detector.util as util

from ..config import INTERIM_DIRECTORY


def process(file_path: Path):
    # Note the use of .stem as opposed to .name, we do not want
    # the extension here,
    filename = file_path.stem
    segments = segment(file_path, INTERIM_DIRECTORY / filename)
    downsamples = list(map(downsample, segments))

    # TODO: Some kind of message object?
    response = {'filename': file_path.name, 'errors': []}

    for frame_paths in downsamples:
        if len(frame_paths) == 0:
            # Happens on rare occasions, for instance Megamind_bugy.avi
            # gets split into 9 segments where the final segment has
            # no length
            continue

        frames = list(map(util.imread, frame_paths))
        keyframe = Keyframe.from_frames(frames)
        video_name = util.video_name_from_path(frame_paths[0])
        segment_id = util.segment_id_from_path(frame_paths[0])

        fpc = FingerprintCollection.from_keyframe(
            keyframe,
            video_name,
            segment_id)

        fpc = FingerprintCollectionModel.from_fingerprint_collection(fpc)

        try:
            db.session.add(fpc)
            db.session.commit()
        except Exception as e:
            logger.error(e)
            response['errors'].append(e)

    return response


def list_processed_files():
    pk_name_tuples = list(db.session.query(
        FingerprintCollectionModel.pk,
        FingerprintCollectionModel.video_name))

    # TODO: Right now this returns a list of all fingerprints...
    # (one per segment)
    return [{'pk': t[0], 'filename': t[1]} for t in pk_name_tuples]
