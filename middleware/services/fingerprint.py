from typing import List

from loguru import logger

from video_reuse_detector.fingerprint import FingerprintComparison
from video_reuse_detector.fingerprint import compare_fingerprints as CF

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
