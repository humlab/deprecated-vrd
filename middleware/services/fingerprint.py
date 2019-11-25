from loguru import logger

from video_reuse_detector.fingerprint import compare_fingerprints as CF

from ..models import db
from ..models.fingerprint_collection import FingerprintCollectionModel
from ..models.fingerprint_comparison import FingerprintComparisonModel

from .profiling import timeit

@timeit
def compare_fingerprints(t):
    query_video_name = t[0]
    reference_video_name = t[1]

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

    all_comparisons = list(
        map(FingerprintComparisonModel.from_fingerprint_comparison, all_comparisons)
    )

    db.session.bulk_save_objects(all_comparisons)
    db.session.commit()

    return True


def fingerprint_collections_for_video_with_name(video_name):
    models = (
        db.session.query(FingerprintCollectionModel)
        .filter_by(video_name=video_name)
        .all()
    )

    return list(map(FingerprintCollectionModel.to_fingerprint_collection, models))
