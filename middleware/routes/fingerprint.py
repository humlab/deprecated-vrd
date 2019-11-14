from flask import Blueprint, request
from loguru import logger

from ..models import db
from ..models.fingerprint_comparison import (
    FingerprintComparisonModel,
    FingerprintComparisonSchema,
)


fingerprint_blueprint = Blueprint('fingerprint', __name__)
fingerprint_schema = FingerprintComparisonSchema(many=True)


@fingerprint_blueprint.route('/compare', methods=['POST'])
def compare():
    # Using POST instead of GET to not run into URL-length limits
    req_data = request.get_json()

    query_video_name = req_data['query_video_name']  # Single video
    reference_video_names = req_data['reference_video_names']  # List of videos

    sql_query = (
        db.session.query(FingerprintComparisonModel)
        .filter_by(query_video_name=query_video_name)
        .filter(
            FingerprintComparisonModel.reference_video_name.in_(reference_video_names)
        )
    )

    logger.trace(sql_query)

    return fingerprint_schema.jsonify(sql_query.all())


def register_as_plugin(app):
    logger.debug('Registering fingerprint_blueprint')
    app.register_blueprint(fingerprint_blueprint, url_prefix='/fingerprints')
