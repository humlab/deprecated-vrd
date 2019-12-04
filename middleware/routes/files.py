from flask import Blueprint, current_app, jsonify, request
from loguru import logger
from werkzeug.utils import secure_filename

from ..models import db
from ..models.video_file import VideoFile
from ..services import files


file_blueprint = Blueprint('file', __name__)


@file_blueprint.route('/list')
def list_files():
    try:
        return jsonify({"files": files.list_files()})
    except Exception as e:
        # Couldn't connect to database or database not seeded
        logger.warning(f"Exception when attempting to list files: {e}")
        return jsonify({"files": []}), 500


@file_blueprint.route('/upload', methods=['POST'])
def upload_file():
    # TODO: pass request.files['file'] directly to files.process?
    f = request.files['file']
    filename = secure_filename(f.filename)
    upload_destination = current_app.config['UPLOAD_DIRECTORY'] / filename
    f.save(str(upload_destination))

    video_name = upload_destination.name
    video_file = db.session.query(VideoFile).filter_by(video_name=video_name).first()

    if video_file:
        logger.warning(f'"{video_name}" already in database, skipping...')
        return f'Rejected "{video_name}" as it already exists', 403

    logger.info(f'Adding "{video_name}" to video_file table')
    db.session.add(VideoFile.from_upload(upload_destination))
    db.session.commit()

    return f'Uploaded {video_name}', 202


def register_as_plugin(app):
    logger.debug('Registering file_blueprint')
    app.register_blueprint(file_blueprint, url_prefix='/api/files')
