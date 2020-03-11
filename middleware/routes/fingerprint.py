import itertools
from collections import defaultdict
from typing import Set, Tuple

from flask import Blueprint, current_app, jsonify, request
from loguru import logger
from sqlalchemy import func

from ..models import db
from ..models.fingerprint_collection import FingerprintCollectionModel
from ..models.fingerprint_comparison import (
    FingerprintComparisonModel,
    FingerprintComparisonSchema,
)
from ..models.video_file import VideoFile, VideoFileState
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

    total_matches = sum(len(matches) for matches in grouped_by_match_level.values())
    d['totalMatches'] = total_matches

    assert d['distinctMatches'] <= d['totalMatches']

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


def comparisons_between(query_video_name, reference_video_name):
    return (
        db.session.query(FingerprintComparisonModel)
        # Since we insert inverted comparison we do not
        # have to worry about ordering here!
        .filter(
            FingerprintComparisonModel.query_video_name == query_video_name,
            FingerprintComparisonModel.reference_video_name == reference_video_name,
        )
    )


def has_comparison(query_video_name, reference_video_name):
    return (
        comparisons_between(query_video_name, reference_video_name).first() is not None
    )


def names_of_fingerprinted_videos(names) -> Set[str]:
    """
    Returns all the names in `names` where there exists a fingerprint
    """
    query = (
        db.session.query(VideoFile.video_name)
        .filter(VideoFile.video_name.in_(names))
        .filter(VideoFile.processing_state == VideoFileState.FINGERPRINTED)
    )

    logger.trace(query)

    result = query.all()

    # Refer to
    #
    # https://sopython.com/canon/115/single-column-query-results-in-a-list-of-tuples-in-sqlalchemy/  # noqa: E501
    return set([v for v, in result])


@fingerprint_blueprint.route('/compare', methods=['POST'])
def compute_comparisons():
    def videos_with_fingerprints(
        query_video_names, reference_video_names
    ) -> Tuple[Set[str], Set[str]]:
        query_videos_ready_to_compare = names_of_fingerprinted_videos(query_video_names)
        reference_videos_ready_to_compare = names_of_fingerprinted_videos(
            reference_video_names
        )

        return (
            query_videos_ready_to_compare,
            reference_videos_ready_to_compare,
        )

    # Using POST instead of GET to not run into URL-length limits
    req_data = request.get_json()

    query_video_names = set(req_data['query_video_names'])  # List of videos
    reference_video_names = set(req_data['reference_video_names'])  # List of videos

    fingerprinted_query_vids, fingerprinted_reference_vids = videos_with_fingerprints(
        query_video_names, reference_video_names
    )

    response = {}

    for query_video_name in fingerprinted_query_vids:
        for reference_video_name in fingerprinted_reference_vids:
            comparison_exists = (
                comparisons_between(query_video_name, reference_video_name).first()
                is not None
            )

            if comparison_exists:
                logger.info(
                    f'Comparison between {query_video_name} and {reference_video_name} exists'  # noqa: E501
                )

                response[f'{query_video_name}/{reference_video_name}'] = 'exists'
            else:
                logger.info(
                    f'Enqueuing comparison between "{query_video_name}" and "{reference_video_name}"'  # noqa: E501
                )
                current_app.compare_queue.enqueue(
                    compare_fingerprints,
                    args=(query_video_name, reference_video_name),
                    job_timeout=6000,
                )
                response[f'{query_video_name}/{reference_video_name}'] = 'started'

    cannot_compare = query_video_names - fingerprinted_query_vids
    cannot_compare |= reference_video_names - fingerprinted_reference_vids

    for unfingerprinted_video in cannot_compare:
        response[f'{unfingerprinted_video}'] = 'fingerprint missing'

    return jsonify(response)


def register_as_plugin(app):
    logger.debug('Registering fingerprint_blueprint')
    app.register_blueprint(fingerprint_blueprint, url_prefix='/api/fingerprints')
