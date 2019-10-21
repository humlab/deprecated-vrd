from flask import Flask, request
from werkzeug.utils import secure_filename
from flask_cors import CORS
from pathlib import Path
import json
import os
from typing import Dict


def unprocessed_file(path: Path) -> Dict[str, str]:
    return {'filename': str(path.name), 'state': 'UNPROCESSED'}


app = Flask(__name__)
CORS(app)

BASE_DIR = Path(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_DIRECTORY = BASE_DIR / 'raw'

if not UPLOAD_DIRECTORY.exists():
    UPLOAD_DIRECTORY.mkdir()

initial_file_names = list(UPLOAD_DIRECTORY.glob('**/*'))
unprocessed_files = list(map(unprocessed_file, initial_file_names))
files = unprocessed_files


@app.route('/')
def hello_world():
    return 'Hello, world!'


@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        filename = secure_filename(f.filename)
        f.save(str(UPLOAD_DIRECTORY / filename))
        files.append({'filename': filename, 'state': 'UNPROCESSED'})

        return '{filename} uploaded successfully!'


@app.route('/list')
def list_files():
    return json.dumps(files)


if __name__ == '__main__':
    app.run()
