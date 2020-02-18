from flask import Blueprint, current_app, request
from loguru import logger

from ..models import db
from ..models.fingerprint_comparison import (
    FingerprintComparisonModel,
    FingerprintComparisonSchema,
)
from ..services.fingerprint import compare_fingerprints


fingerprint_blueprint = Blueprint('fingerprint', __name__)
fingerprint_schema = FingerprintComparisonSchema(many=True)


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
    )

    logger.trace(sql_query)

    return fingerprint_schema.jsonify(sql_query.all())


@fingerprint_blueprint.route('/compare', methods=['POST'])
def compute_comparisons():
    # Using POST instead of GET to not run into URL-length limits
    req_data = request.get_json()

    query_video_names = req_data['query_video_names']  # List of videos
    reference_video_names = req_data['reference_video_names']  # List of videos

    # TODO: Fail for videos that do not have fingerprints yet
    for query_video_name in query_video_names:
        for reference_video_name in reference_video_names:
            t = (query_video_name, reference_video_name)
            logger.info(f'Enqueuing comparison between "{t[0]}" and "{t[1]}"')
            current_app.compare_queue.enqueue(compare_fingerprints, t, job_timeout=6000)

    return 'Computations started', 200


def register_as_plugin(app):
    logger.debug('Registering fingerprint_blueprint')
    app.register_blueprint(fingerprint_blueprint, url_prefix='/api/fingerprints')
