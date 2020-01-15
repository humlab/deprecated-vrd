from pathlib import Path
from typing import List

from loguru import logger

from video_reuse_detector import ffmpeg, util
from video_reuse_detector.downsample import downsample
from video_reuse_detector.fingerprint import (
    FingerprintCollection,
    FingerprintComparison,
)
from video_reuse_detector.fingerprint import compare_fingerprints as CF
from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.segment import segment

from ..config import INTERIM_DIRECTORY
from ..models import db
from ..models.fingerprint_collection import FingerprintCollectionModel
from ..models.fingerprint_collection_computation import FingerprintCollectionComputation
from ..models.fingerprint_comparison import FingerprintComparisonModel
from ..models.fingerprint_comparison_computation import FingerprintComparisonComputation
from .profiling import timeit


def invert_fingerprint_comparison(fc: FingerprintComparison) -> FingerprintComparison:
    return FingerprintComparison(
        query_video_name=fc.reference_video_name,
        reference_video_name=fc.query_video_name,
        query_segment_id=fc.reference_segment_id,
        reference_segment_id=fc.query_segment_id,
        match_level=str(fc.match_level),
        similarity_score=fc.similarity_score,
    )


@timeit
def __extract_fingerprint_collections__(file_path: Path) -> List[FingerprintCollection]:
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

        keyframe = Keyframe.from_frame_paths(frame_paths)
        segment_id = util.segment_id_from_path(frame_paths[0])

        fps.append(
            FingerprintCollection.from_keyframe(keyframe, file_path.name, segment_id)
        )

    return fps


def __extract_fingerprints__(file_path: Path) -> Path:
    assert file_path.exists()

    fingerprints, processing_time = __extract_fingerprint_collections__(file_path)
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

    return file_path


def extract_fingerprints(file_path: str) -> Path:
    return __extract_fingerprints__(Path(file_path))


@timeit
def __compare_fingerprints__(
    query_video_name, reference_video_name
) -> List[FingerprintComparison]:
    # One per segment
    query_fps = fingerprint_collections_for_video_with_name(query_video_name)
    reference_fps = fingerprint_collections_for_video_with_name(reference_video_name)

    all_comparisons = []

    for query_fp in query_fps:
        for reference_fp in reference_fps:
            logger.info(
                f'Comparing {query_fp.video_name}:{query_fp.segment_id} to {reference_fp.video_name}:{reference_fp.segment_id}'  # noqa: E501
            )

            all_comparisons.append(CF(query_fp, reference_fp))

    return all_comparisons


"""
def compute_comparisons(name):
    # This is a list of single-element tuples
    video_names = db.session.query(FingerprintCollectionModel.video_name).all()

    # Unpack the tuples as per
    # https://sopython.com/canon/115/single-column-query-results-in-a-list-of-tuples-in-sqlalchemy/  # noqa: E501
    video_names = [video_name for video_name, in video_names]

    # Remove duplicates, this wouldn't be necessary if we used an auxiliary table
    # and SQL events,
    video_names = list(set(video_names))

    # No need to compare the input video against itself
    reference_videos = filter(lambda video_name: video_name != name, video_names)

    with Connection(redis_connection):
        compare_queue = Queue(COMPARE_QUEUE_NAME)
        for reference_video_name in reference_videos:
            logger.info(f"Enqueue comparing ({name}, {reference_video_name})")
            assert reference_video_name != name

            compare_queue.enqueue(
                fingerprint.compare_fingerprints, (name, reference_video_name)
            )
"""


def get_video_duration(video_name: str) -> float:
    return db.session.query(FingerprintCollectionComputation.video_duration).filter_by(
        video_name=video_name
    )


def model_from_comparison(fpc: FingerprintComparison) -> FingerprintComparisonModel:
    return FingerprintComparisonModel.from_fingerprint_comparison(fpc)


def compare_fingerprints(t):
    query_video_name = t[0]
    reference_video_name = t[1]

    all_comparisons, processing_time = __compare_fingerprints__(
        query_video_name, reference_video_name
    )
    all_comparisons_inverted = list(map(invert_fingerprint_comparison, all_comparisons))
    all_comparisons = all_comparisons + all_comparisons_inverted

    # TODO: Can possibly associate computations to object through db.relationship?
    query_video_duration = get_video_duration(query_video_name)
    reference_video_duration = get_video_duration(reference_video_name)

    comparison_models = list(map(model_from_comparison, all_comparisons))
    db.session.bulk_save_objects(comparison_models)

    # TODO: should be bidirectional also?
    db.session.add(
        FingerprintComparisonComputation(
            query_video_name=query_video_name,
            reference_video_name=reference_video_name,
            query_video_duration=query_video_duration,
            reference_video_duration=reference_video_duration,
            processing_time=processing_time,
        )
    )

    db.session.commit()

    return True


def fingerprint_collections_for_video_with_name(video_name):
    models = (
        db.session.query(FingerprintCollectionModel)
        .filter_by(video_name=video_name)
        .all()
    )

    return list(map(FingerprintCollectionModel.to_fingerprint_collection, models))
