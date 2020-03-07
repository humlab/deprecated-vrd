import itertools
from collections import defaultdict

from flask import Blueprint, current_app, jsonify, request
from loguru import logger
from sqlalchemy import func

from ..models import db
from ..models.fingerprint_collection import FingerprintCollectionModel
from ..models.fingerprint_comparison import (
    FingerprintComparisonModel,
    FingerprintComparisonSchema,
)
from ..services.fingerprint import compare_fingerprints


fingerprint_blueprint = Blueprint('fingerprint', __name__)
fingerprint_schema = FingerprintComparisonSchema(many=True)


def groupby_to_dict(iterable, grouper):
    return {k: list(v) for k, v in itertools.groupby(iterable, grouper)}


def group_by_name_pairing(fpcms):
    def __group_by_name_pairing__(fpcm):
        return (fpcm.query_video_name, fpcm.reference_video_name)

    return groupby_to_dict(fpcms, __group_by_name_pairing__)


def group_by_match_level(fpcms):
    grouped_by_match_level = defaultdict(list)

    for fpcm in fpcms:
        grouped_by_match_level[fpcm.match_level].append(fpcm)

    return grouped_by_match_level


def fetch_number_of_segments_for_video(video_name: str) -> int:
    return (
        db.session.query(func.count(FingerprintCollectionModel.pk))
        .filter(FingerprintCollectionModel.video_name == video_name)
        .one()[0]
    )


def structure_fingerprint_comparison_information(
    fpcms, query_video_name, reference_video_name
):
    d = {}

    grouped_by_match_level = group_by_match_level(fpcms)

    d['comparisons'] = {
        match_level: fingerprint_schema.dump(comparisons)
        for match_level, comparisons in grouped_by_match_level.items()
    }
    d['numberOfQuerySegments'] = fetch_number_of_segments_for_video(query_video_name)
    d['numberOfReferenceSegments'] = fetch_number_of_segments_for_video(
        reference_video_name
    )

    # Distinct matches
    query_segments_with_match = set(fpcm.query_segment_id for fpcm in fpcms)
    reference_segments_with_match = set(fpcm.reference_segment_id for fpcm in fpcms)
    distinct_matches = len(query_segments_with_match) + len(
        reference_segments_with_match
    )
    d['distinctMatches'] = distinct_matches

    total_matches = sum(len(matches) for matches in grouped_by_match_level)
    d['totalMatches'] = total_matches

    return d


@fingerprint_blueprint.route('/comparisons', methods=['POST'])
def get_comparisons():
    # Using POST instead of GET to not run into URL-length limits
    req_data = request.get_json()

    query_video_names = req_data['query_video_names']  # List of videos
    reference_video_names = req_data['reference_video_names']  # List of videos

    logger.info(
        f'Retrieving comparisons between "{query_video_names}" and "{reference_video_names}""'  # noqa: E501
    )

    sql_query = (
        db.session.query(FingerprintComparisonModel)
        .filter(FingerprintComparisonModel.query_video_name.in_(query_video_names))
        .filter(
            FingerprintComparisonModel.reference_video_name.in_(reference_video_names)
        )
        .filter(FingerprintComparisonModel.similarity_score > 0)
    )

    logger.trace(sql_query)

    db_result = sql_query.all()

    comparisons_grouped_by_name_pairing = group_by_name_pairing(db_result)
    enriched_comparisons = []

    for name_pair, fpcms_by_name in comparisons_grouped_by_name_pairing.items():
        query_video_name = name_pair[0]
        reference_video_name = name_pair[1]

        comparison = structure_fingerprint_comparison_information(
            fpcms_by_name, query_video_name, reference_video_name
        )

        comparison['queryVideoName'] = query_video_name
        comparison['referenceVideoName'] = reference_video_name

        enriched_comparisons.append(comparison)

    return jsonify({'comparisons': enriched_comparisons})


@fingerprint_blueprint.route('/compare', methods=['POST'])
def compute_comparisons():
    # Using POST instead of GET to not run into URL-length limits
    req_data = request.get_json()

    query_video_names = req_data['query_video_names']  # List of videos
    reference_video_names = req_data['reference_video_names']  # List of videos

    # TODO: Fail for videos that do not have fingerprints yet
    for query_video_name in query_video_names:
        for reference_video_name in reference_video_names:
            logger.info(
                f'Enqueuing comparison between "{query_video_name}" and "{reference_video_name}"'  # noqa: E501
            )
            current_app.compare_queue.enqueue(
                compare_fingerprints,
                args=(query_video_name, reference_video_name),
                job_timeout=6000,
            )

    return 'Computations started', 200


def register_as_plugin(app):
    logger.debug('Registering fingerprint_blueprint')
    app.register_blueprint(fingerprint_blueprint, url_prefix='/api/fingerprints')
