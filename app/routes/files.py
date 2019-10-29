from werkzeug.utils import secure_filename
from flask import request, Blueprint
import json

import concurrent.futures

from ..services import files

from . import socketio
from ..config import UPLOAD_DIRECTORY

file_api = Blueprint('file_api', __name__)
executor = concurrent.futures.ProcessPoolExecutor(max_workers=4)


@file_api.route('/list')
def list_files():
    return json.dumps(files.list_processed_files())


@file_api.route('/upload', methods=['POST'])
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
    name = result['filename']

    if isinstance(result, Exception):
        socketio.emit('state_change', {'name': name, 'state': 'ERROR'})
    else:
        socketio.emit('state_change', {'name': name, 'state': 'PROCESSED'})


def register_as_plugin(app):
    app.register_blueprint(file_api, url_prefix='/files')
