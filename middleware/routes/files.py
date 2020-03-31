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

import middleware.models.video_file as video_file

from ..models import db
from ..models.video_file import VideoFile, VideoFileType
from ..services import files


file_blueprint = Blueprint('file', __name__)


@file_blueprint.route("/uploads/<path:filename>")
def uploadfiles(filename):
    return send_from_directory(current_app.config["UPLOADS_DIRECTORY"], filename)


@file_blueprint.route("/archive/<path:filename>")
def archivefiles(filename):
    return send_from_directory(current_app.config["ARCHIVE_DIRECTORY"], filename)


@file_blueprint.route("/info/<path:filename>")
def info(filename):
    return jsonify({'file': files.info(filename)})


@file_blueprint.route('/list')
def list_files():
    try:
        return jsonify({"files": files.list_files()})
    except Exception as e:
        # Couldn't connect to database or database not seeded
        logger.warning(f"Exception when attempting to list files: {e}")
        return jsonify({"files": []}), 500


def generate_random_filename(extension):
    import random_name

    return f'{random_name.generate_name()}{extension}'


@file_blueprint.route('/upload', methods=['POST'])
def upload_file():
    FORM_PROPERTY_FILE_TYPE = 'file_type'

    if request.form.get(FORM_PROPERTY_FILE_TYPE) is None:
        return f'Expected attribute "{FORM_PROPERTY_FILE_TYPE}" to be set', 400

    def get_target_directory(file_type):
        expected_filetypes_to_dir_map = {
            VideoFileType.QUERY: current_app.config['UPLOADS_DIRECTORY'],
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
    display_name = f.filename

    if db.session.query(VideoFile).filter_by(display_name=display_name).first():
        logger.warning(f'"{display_name}" already in database, skipping...')
        return f'Rejected "{display_name}" as it already exists', 403

    # NOTE: Does not contain the extension! However, we cannot perform the
    # assertion
    #
    # assert extension not in ascii_only_filename
    #
    # as this is an example of a valid filename: Ｊａｇｕａｒ．ｍｐ４.mp4
    ascii_only_filename = secure_filename(Path(display_name).stem)
    extension = Path(display_name).suffix

    # The uploaded file must have been all non-ASCII characters,
    if ascii_only_filename == '':
        # Note that filename here contains the extension
        filename = generate_random_filename(extension)

        # so this filter_by is "safe"
        is_unique = (
            db.session.query(VideoFile).filter_by(video_name=filename).first() is None
        )

        while not is_unique:
            filename = generate_random_filename(extension)
            is_unique = (
                db.session.query(VideoFile).filter_by(video_name=filename).first()
                is None
            )
    else:
        filename = f'{ascii_only_filename}{extension}'

    if db.session.query(VideoFile).filter_by(video_name=filename).first():
        logger.warning(f'"{filename}" already in database, skipping...')
        return f'Rejected "{filename}" as it already exists', 403

    target_directory = get_target_directory(file_type)
    upload_destination = target_directory / filename

    logger.info(f'Saving upload to {str(upload_destination)}')
    f.save(str(upload_destination))

    assert upload_destination.exists()

    video_name = upload_destination.name

    def create_video_file(
        display_name: str, upload_destination: Path, file_type: VideoFileType
    ) -> VideoFile:
        if file_type == VideoFileType.QUERY:
            return VideoFile.from_upload(upload_destination, display_name)
        elif file_type == VideoFileType.REFERENCE:
            return VideoFile.from_archival_footage(upload_destination, display_name)
        else:
            # Should never happen, handled by .from_str earlier
            raise NotImplementedError

    logger.info(f'Adding "{video_name}" to video_file table')
    db_video_file = create_video_file(display_name, upload_destination, file_type)
    db.session.add(db_video_file)
    video_file.after_insert(db_video_file)
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
