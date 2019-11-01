from loguru import logger
from pathlib import Path
from typing import Set

from ..models import db
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
    response = {'name': file_path.name, 'errors': []}

    for frame_paths in downsamples:
        if len(frame_paths) == 0:
            # Happens on rare occasions, for instance Megamind_bugy.avi
            # gets split into 9 segments where the final segment has
            # no length
            continue

        frames = list(map(util.imread, frame_paths))
        keyframe = Keyframe.from_frames(frames)
        segment_id = util.segment_id_from_path(frame_paths[0])

        fpc = FingerprintCollection.from_keyframe(
            keyframe,
            file_path.name,
            segment_id)

        fpc = FingerprintCollectionModel.from_fingerprint_collection(fpc)

        try:
            db.session.add(fpc)
            db.session.commit()
        except Exception as e:
            logger.error(e)
            response['errors'].append(str(e))  # type: ignore

    return response


def list_processed_files() -> Set[str]:
    query = db.session.query(FingerprintCollectionModel.video_name)

    # This is a list of single-element tuples, where every tuple in the list is
    # of length 1. The tuples are single-element because we query for a
    # single column.
    list_of_tuples = list(query)

    # Unpack the single-element tuples, transforming [('some_name.avi',),...]
    # into a list on the form ['some_name.avi',...]
    list_of_names = [t[0] for t in list_of_tuples]

    # The list contains duplicates, as we are querying for fingerprint
    # collections and we have such a collection for every segment for each
    # video.
    return set(list_of_names)
