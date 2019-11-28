from flask import Blueprint, current_app, jsonify, request
from flask_socketio import SocketIO
from loguru import logger
from rq import Connection, Queue
from werkzeug.utils import secure_filename

from ..models import db
from ..models.fingerprint_collection import FingerprintCollectionModel
from ..services import files, fingerprint
from ..workers import REDIS_URL, redis_connection
from ..workers.fingerprint_comparator import COMPARE_QUEUE_NAME
from ..workers.fingerprint_extractor import EXTRACT_QUEUE_NAME


file_blueprint = Blueprint('file', __name__)
socketio = None


@file_blueprint.route('/list')
def list_files():
    try:
        # list() to make the return value JSON-serializable
        return jsonify(list(files.list_processed_files()))
    except Exception as e:
        # Couldn't connect to database or database not seeded
        logger.warning(f"Exception when attempting to list files: {e}")

        # TODO: Return a 500 or something, or split our results into a
        # status/data type message object.
        return jsonify([])


@file_blueprint.route('/upload', methods=['POST'])
def upload_file():
    # TODO: pass request.files['file'] directly to files.process?
    f = request.files['file']
    filename = secure_filename(f.filename)
    upload_destination = current_app.config['UPLOAD_DIRECTORY'] / filename
    f.save(str(upload_destination))

    with Connection(redis_connection):
        extract_queue = Queue(EXTRACT_QUEUE_NAME)
        process_job = extract_queue.enqueue(
            files.process, upload_destination, at_front=True
        )
        extract_queue.enqueue(
            mark_as_done, upload_destination.name, depends_on=process_job
        )

        # TODO: Do not initiate compare on upload
        compare_queue = Queue(COMPARE_QUEUE_NAME)
        compare_queue.enqueue(
            compute_comparisons, upload_destination.name, depends_on=process_job
        )

    return f'Processing {filename}'


def mark_as_done(name):
    SocketIO(message_queue=REDIS_URL).emit(
        'state_change', {'name': name, 'state': 'PROCESSED'}
    )


def compute_comparisons(name):
    """
    TODO: This can arguably be solved using events, rather than depends_on,
    but would necessitate the use of an additional table hosting names of
    completed collections as the following is executed for each row insertion,

    from sqlalchemy import event

    @event.listens_for(FingerprintCollectionModel, 'after_insert')
    def receive_after_insert(mapper, connection, target):
        # Do stuff

    so maybe if we introduce another table for that it could be done rather
    cleanly.
    """
    # This is a list of single-element tuples
    video_names = db.session.query(FingerprintCollectionModel.video_name).all()

    # Unpack the tuples as per
    # https://sopython.com/canon/115/single-column-query-results-in-a-list-of-tuples-in-sqlalchemy/  # noqa: E501
    video_names = [video_name for video_name, in video_names]

    # Remove duplicates, this wouldn't be necessary if we used an auxiliary table
    # and SQL events,
    video_names = list(set(video_names))

    # No need to compare the input video against itself
    reference_videos = filter(lambda video_name: video_name != name, video_names)

    with Connection(redis_connection):
        compare_queue = Queue(COMPARE_QUEUE_NAME)
        for reference_video_name in reference_videos:
            logger.info(f"Enqueue comparing ({name}, {reference_video_name})")
            assert reference_video_name != name

            compare_queue.enqueue(
                fingerprint.compare_fingerprints, (name, reference_video_name)
            )


def register_as_plugin(app):
    logger.debug('Registering file_blueprint')
    app.register_blueprint(file_blueprint, url_prefix='/api/files')


def open_websocket(app):
    global socketio

    if socketio is None:
        logger.debug('Opening websocket')

        # Note: local development will not work without cors_allowed_origins="*"
        socketio = SocketIO(app, cors_allowed_origins="*", message_queue=REDIS_URL)
    else:
        logger.warning('Websocket already open! Doing nothing...')
