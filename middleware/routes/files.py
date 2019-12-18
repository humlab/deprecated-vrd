import json
from pathlib import Path

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    request,
    send_from_directory,
)
from loguru import logger
from werkzeug.utils import secure_filename

from ..models import db
from ..models.video_file import VideoFile, VideoFileType
from ..services import files


file_blueprint = Blueprint('file', __name__)


@file_blueprint.route("/uploads/<path:filename>")
def uploadfiles(filename):
    return send_from_directory(current_app.config["UPLOAD_DIRECTORY"], filename)


@file_blueprint.route("/archive/<path:filename>")
def archivefiles(filename):
    return send_from_directory(current_app.config["ARCHIVE_DIRECTORY"], filename)


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
    FORM_PROPERTY_FILE_TYPE = 'file_type'

    if request.form.get(FORM_PROPERTY_FILE_TYPE) is None:
        return f'Expected attribute "{FORM_PROPERTY_FILE_TYPE}" to be set', 400

    def get_target_directory(file_type):
        expected_filetypes_to_dir_map = {
            VideoFileType.QUERY: current_app.config['UPLOAD_DIRECTORY'],
            VideoFileType.REFERENCE: current_app.config['ARCHIVE_DIRECTORY'],
        }

        return expected_filetypes_to_dir_map[file_type]

    file_type = None

    try:
        file_type = VideoFileType.from_str(request.form[FORM_PROPERTY_FILE_TYPE])
    except ValueError as e:
        return str(e), 400

    assert file_type

    if not request.files:
        return (
            (
                'No file available in the request. Did the request have '
                'enctype="multipart/form-data"?'
            ),
            400,
        )

    f = request.files['file']
    filename = secure_filename(f.filename)

    target_directory = get_target_directory(file_type)
    upload_destination = target_directory / filename
    f.save(str(upload_destination))

    video_name = upload_destination.name

    # TODO: enforce uniqueness on name/type pairing and not just name
    video_file = db.session.query(VideoFile).filter_by(video_name=video_name).first()

    if video_file:
        logger.warning(f'"{video_name}" already in database, skipping...')
        return f'Rejected "{video_name}" as it already exists', 403

    def create_video_file(
        upload_destination: Path, file_type: VideoFileType
    ) -> VideoFile:
        if file_type == VideoFileType.QUERY:
            return VideoFile.from_upload(upload_destination)
        elif file_type == VideoFileType.REFERENCE:
            return VideoFile.from_archival_footage(upload_destination)
        else:
            raise NotImplementedError

    logger.info(f'Adding "{video_name}" to video_file table')
    db.session.add(create_video_file(upload_destination, file_type))
    db.session.commit()

    return Response(
        json.dumps(
            {
                'video_name': video_name,
                'file_type': file_type.name,
                'target_directory': str(target_directory),
            }
        ),
        status=202,
        mimetype='application/json',
    )


def register_as_plugin(app):
    logger.debug('Registering file_blueprint')
    app.register_blueprint(file_blueprint, url_prefix='/api/files')
