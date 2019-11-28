from pathlib import Path
from typing import Dict, List

from loguru import logger

import video_reuse_detector.ffmpeg as ffmpeg
import video_reuse_detector.util as util
from video_reuse_detector.downsample import downsample
from video_reuse_detector.fingerprint import FingerprintCollection
from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.segment import segment

from ..config import INTERIM_DIRECTORY
from ..models import db
from ..models.fingerprint_collection import FingerprintCollectionModel
from ..models.fingerprint_collection_computation import FingerprintCollectionComputation
from ..models.video_file import VideoFile
from .profiling import timeit


@timeit
def extract_fingerprints(file_path: Path) -> List[FingerprintCollection]:
    # Note the use of .stem as opposed to .name, we do not want
    # the extension here,
    segments = segment(file_path, INTERIM_DIRECTORY / file_path.stem)
    downsamples = list(map(downsample, segments))

    fps = []

    for frame_paths in downsamples:
        if len(frame_paths) == 0:
            # Happens on rare occasions, for instance Megamind_bugy.avi
            # gets split into 9 segments where the final segment has
            # no length
            continue

        frames = list(map(util.imread, frame_paths))
        keyframe = Keyframe.from_frames(frames)
        segment_id = util.segment_id_from_path(frame_paths[0])

        fps.append(
            FingerprintCollection.from_keyframe(keyframe, file_path.name, segment_id)
        )

    return fps


def process(file_path: Path):  # TODO: move to fingerprints.py
    assert file_path.exists()

    fingerprints, processing_time = extract_fingerprints(file_path)
    models = list(
        map(FingerprintCollectionModel.from_fingerprint_collection, fingerprints)
    )

    db.session.bulk_save_objects(models)

    duration = ffmpeg.get_video_duration(file_path)
    filename = file_path.name

    db.session.add(
        FingerprintCollectionComputation(
            video_name=filename,
            video_duration=duration,
            processing_time=processing_time,
        )
    )

    db.session.commit()

    logger.info(
        f'Processing {filename} ({duration} seconds of video) took {processing_time}s seconds'  # noqa: E501
    )

    return filename


def list_files() -> Dict[str, str]:
    query = db.session.query(VideoFile.video_name, VideoFile.processing_state)

    # This is a list of two-element tuples, (video_name, processing_state)
    list_of_tuples = list(query)

    # Unpack the single-element tuples, transforming
    #
    # [('some_name.avi', 'FINGERPRINTED'),...]
    #
    # into a dictionary on the form {'some_name.avi': 'FINGERPRINTED',...}
    #
    # Note that the states are in an enum representation, hence .name
    d = {t[0]: t[1].name for t in list_of_tuples}

    return d
