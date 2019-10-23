from flask import Flask, request
from werkzeug.utils import secure_filename
from flask_cors import CORS
from pathlib import Path
import json
import os
from typing import Dict
from video_reuse_detector.segment import segment
from video_reuse_detector.downsample import downsample
from video_reuse_detector.keyframe import Keyframe
from loguru import logger
import threading
import cv2


def unprocessed_file(path: Path) -> Dict[str, str]:
    return {'filename': str(path.name), 'state': 'UNPROCESSED'}


def create_directory(path: Path):
    if not path.exists():
        path.mkdir()

    return path


app = Flask(__name__)
CORS(app)

BASE_DIR = Path(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_DIRECTORY = create_directory(BASE_DIR / 'raw')
INTERIM_DIRECTORY = create_directory(BASE_DIR / 'interim')
PROCESSED_DIRECTORY = create_directory(BASE_DIR / 'processed')

initial_file_names = list(UPLOAD_DIRECTORY.glob('**/*'))

files = {}
for path in initial_file_names:
    files[path.name] = unprocessed_file(path)


def process_upload(upload_path: Path):
    # Note the use of .stem as opposed to .name, we do not want
    # the extension here,
    filename = upload_path.stem
    segments = segment(upload_path, INTERIM_DIRECTORY / filename)
    downsamples = list(map(downsample, segments))

    # TODO: 1. Why is this not observable in main thread (see 2)
    files[upload_path.name]['state'] = 'PROCESSING'

    for group_of_frames in downsamples:
        cv2_compatible_paths = list(map(str, group_of_frames))
        frames = list(map(cv2.imread, cv2_compatible_paths))
        keyframe = Keyframe.from_frames(frames)

        # Determine write destination by using the path to the
        # first input image (this is "safe" because all paths
        # within the group are assumed to belong to the same segment),
        # which we verify here,
        def has_parent_equal_to(p, parent): return p.parent == parent
        parent = group_of_frames[0].parent

        if not all(has_parent_equal_to(p, parent) for p in group_of_frames):
            # TODO: Mark file as failed to process. Somewhere there is a
            # programming error, also escape processing appropriately
            logger.warning((f'Expected all paths in {group_of_frames}'
                            ' to have same parent directory'))

        # so postulate you have a set of frame paths such as,
        #
        # group_of_frames[0] path/to/interim/Megamind/segment/010/frame001.png
        # group_of_frames[1] path/to/interim/Megamind/segment/010/frame002.png
        # ...
        #
        # then group_of_frames[0].parent is equal to,
        #
        # "path/to/interim/Megamind/segment/010/"
        #
        # and then our destination is that same path except we
        # replace "interim" with "processed"
        destination_path = str(group_of_frames[0].parent / 'keyframe.png')
        destination_path = destination_path.replace(str(INTERIM_DIRECTORY),
                                                    str(PROCESSED_DIRECTORY))

        # TODO: 2. Considering that this is observable in main thread
        files[upload_path.name]['state'] = 'PROCESSED'
        cv2.imwrite(destination_path, keyframe.image)


@app.route('/')
def hello_world():
    return 'Hello, world!'


@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        filename = secure_filename(f.filename)
        upload_destination = UPLOAD_DIRECTORY / filename
        f.save(str(upload_destination))

        key = Path(filename).name
        files[key] = {'filename': Path(filename).name, 'state': 'UNPROCESSED'}

        thread = threading.Thread(
            target=process_upload, args=[upload_destination])
        thread.daemon = True
        thread.start()

        return '{filename} uploaded successfully!'


@app.route('/list')
def list_files():
    return json.dumps(list(files.values()))


if __name__ == '__main__':
    app.run()
