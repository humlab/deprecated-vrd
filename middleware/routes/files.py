import concurrent.futures
import json

from flask import Blueprint, request
from flask_socketio import SocketIO
from loguru import logger
from werkzeug.utils import secure_filename

from ..config import UPLOAD_DIRECTORY
from ..services import files


file_blueprint = Blueprint('file', __name__)
executor = concurrent.futures.ProcessPoolExecutor(max_workers=4)

socketio = None


@file_blueprint.route('/list')
def list_files():
    try:
        # list() to make the return value JSON-serializable
        return json.dumps(list(files.list_processed_files()))
    except Exception as e:
        # Couldn't connect to database or database not seeded
        logger.warning(f"Exception when attempting to list files: {e}")

        # TODO: Return a 500 or something, or split our results into a
        # status/data type message object.
        return json.dumps([])


@file_blueprint.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # TODO: pass request.files['file'] directly to files.process?
        f = request.files['file']
        filename = secure_filename(f.filename)
        upload_destination = UPLOAD_DIRECTORY / filename
        f.save(str(upload_destination))

        future = executor.submit(files.process, upload_destination)
        future.add_done_callback(mark_as_done)

        return f'Processing {filename}'


def mark_as_done(future):
    result = future.result()
    name = result['name']

    if isinstance(result, Exception):
        socketio.emit('state_change', {'name': name, 'state': 'ERROR'})
    else:
        socketio.emit('state_change', {'name': name, 'state': 'PROCESSED'})


def register_as_plugin(app):
    logger.debug('Registering file_blueprint')
    app.register_blueprint(file_blueprint, url_prefix='/files')


def open_websocket(app):
    global socketio

    if socketio == None:
        logger.debug('Opening websocket')
        socketio = SocketIO(app, cors_allowed_origins="*")
    else:
        logger.warning('Websocket already open! Doing nothing...')
