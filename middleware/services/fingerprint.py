import itertools
from pathlib import Path
from typing import List

from loguru import logger

import middleware.models.fingerprint_comparison_computation as fingerprint_comparison_computation  # noqa: E501
from video_reuse_detector import ffmpeg
from video_reuse_detector.fingerprint import (
    FingerprintCollection,
    FingerprintComparison,
    extract_fingerprint_collection,
)
from video_reuse_detector.profiling import timeit

from ..config import INTERIM_DIRECTORY
from ..models import db
from ..models.fingerprint_collection import FingerprintCollectionModel
from ..models.fingerprint_collection_computation import FingerprintCollectionComputation
from ..models.fingerprint_comparison import FingerprintComparisonModel
from ..models.fingerprint_comparison_computation import FingerprintComparisonComputation


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
def __extract_fingerprint_collection__(file_path: Path) -> List[FingerprintCollection]:
    return extract_fingerprint_collection(file_path, INTERIM_DIRECTORY)


def __extract_fingerprints__(file_path: Path) -> Path:
    if not file_path.exists():
        msg = (
            f'Attempted to extract fingerprints for file_path={file_path}'
            f' but file did not exist. Parent directory={file_path.parent}'
            f' satisifes file_path.parent.exists()={file_path.parent.exists()}'
        )

        logger.error(msg)

        if file_path.parent.exists():
            logger.debug(f'Available files in {file_path.parent}')

            for f in file_path.parent.iterdir():
                logger.debug(f)

        raise ValueError(msg)

    assert file_path.exists()

    fingerprints, processing_time = __extract_fingerprint_collection__(file_path)
    models = list(
        map(FingerprintCollectionModel.from_fingerprint_collection, fingerprints)
    )

    db.session.bulk_save_objects(models)

    duration = ffmpeg.get_video_duration(file_path)
    filename = file_path.name

    # TODO: Add if the video has color, and its dimensions, to be able to
    # gauge how video size and color content affect computation time
    db.session.add(
        FingerprintCollectionComputation(
            video_name=filename,
            video_duration=duration,
            processing_time=processing_time,
        )
    )

    db.session.commit()

    logger.success(
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

    # Yields a map wherein each key is a segment in the query video and the value
    # is a list of comparisons to each segment in the reference video. We must
    # flatten all the values
    sorted_comparisons = FingerprintComparison.compare_all(query_fps, reference_fps)

    return list(itertools.chain(*sorted_comparisons.values()))


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
    fpcc = FingerprintComparisonComputation(
        query_video_name=query_video_name,
        reference_video_name=reference_video_name,
        query_video_duration=query_video_duration,
        reference_video_duration=reference_video_duration,
        processing_time=processing_time,
    )

    db.session.add(fpcc)
    db.session.commit()
    fingerprint_comparison_computation.after_insert(fpcc)

    return True


def fingerprint_collections_for_video_with_name(video_name):
    models = (
        db.session.query(FingerprintCollectionModel)
        .filter_by(video_name=video_name)
        .all()
    )

    return list(map(FingerprintCollectionModel.to_fingerprint_collection, models))
