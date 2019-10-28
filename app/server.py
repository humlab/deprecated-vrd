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
from video_reuse_detector.fingerprint import FingerprintCollection
from video_reuse_detector.color_correlation import ColorCorrelation 
import video_reuse_detector.util as util
from loguru import logger
import cv2
import concurrent.futures
from flask_socketio import SocketIO
from .config import BASE_DIR
from flask_sqlalchemy import SQLAlchemy
import base64
import numpy as np


def unprocessed_file(path: Path) -> Dict[str, str]:
    return {'filename': str(path.name), 'state': 'UNPROCESSED'}


def create_directory(path: Path):
    if not path.exists():
        path.mkdir()

    return path


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

base_dir_path = Path(BASE_DIR)
UPLOAD_DIRECTORY = create_directory(base_dir_path / 'raw')
INTERIM_DIRECTORY = create_directory(base_dir_path / 'interim')
PROCESSED_DIRECTORY = create_directory(base_dir_path / 'processed')

initial_file_names = list(UPLOAD_DIRECTORY.glob('**/*'))

files = {}
for path in initial_file_names:
    files[path.name] = unprocessed_file(path)

# TODO: Gracefully clean-up resources
executor = concurrent.futures.ProcessPoolExecutor(max_workers=4)


# TODO: Move to models.py or similar
class FingerprintCollectionModel(db.Model):
    __tablename__ = 'fingerprints'

    pk = db.Column(db.Integer(), primary_key=True)

    # TODO: The keyframe serves no functional purpose
    # once the other fingerprints have been computed
    # and only has value from a debugging stand-point.
    # See commit "4251f77" for reference
    #
    # If kept, either base64 encode it as we do with
    # the thumbnail _or_ capture a path to the keyframe
    # from which we can load it whenever necessary.
    #
    # keyframe = sa.Column(sa.String())
    video_name = db.Column(db.String())
    segment_id = db.Column(db.Integer())
    thumbnail = db.Column(db.String())  # base64
    color_correlation = db.Column(db.BigInteger())
    orb = db.Column(db.ARRAY(db.Integer(), dimensions=2))

    def __init__(self, video_name, segment_id, thumbnail, color_correlation, orb):
        self.video_name = video_name
        self.segment_id = segment_id
        self.thumbnail = thumbnail
        self.color_correlation = color_correlation
        self.orb = orb

    def __repr__(self):
        return '<pk {}>'.format(self.pk)

    def serialize(self):
        return {
            'pk': self.pk,
            'video_name': self.video_name,
            'segment_id': self.segment_id,
            'thumbnail': self.thumbnail,
            'color_correlation': self.color_correlation,
            'orb': self.orb,
        }

    def to_fingerprint_collection(self) -> FingerprintCollection:
        encoded = self.thumbnail
        decoded = base64.b64decode(encoded)
        thumbnail = np.frombuffer(decoded, dtype=np.uint8)

        # TODO: Thumbnails aren't guaranteed to be this size
        # right now. Expose class constant for defaults?
        thumbnail.resize((30, 30, 3))

        cc = ColorCorrelation.from_number(self.color_correlation)

        return FingerprintCollection(
            thumbnail,
            cc,
            np.array(self.orb, dtype=np.uint8),
            self.video_name,
            self.segment_id
        )

    @staticmethod
    def from_fingerprint_collection(fpc: FingerprintCollection):
        video_name = fpc.video_name
        segment_id = fpc.segment_id 
        np_thumb = fpc.thumbnail.image
        encoded = base64.b64encode(np_thumb)
        color_correlation = fpc.color_correlation.as_number
        orb = None
        if fpc.orb is not None:
            orb = fpc.orb.descriptors.tolist()

        return FingerprintCollectionModel(
            video_name, 
            segment_id, 
            encoded, 
            color_correlation,
            orb)


# TODO: Move elsewhere, allowing server.py to essentially be nothing
# but setup and conceivably its routes.
def process_upload(upload_path: Path):
    # Note the use of .stem as opposed to .name, we do not want
    # the extension here,
    filename = upload_path.stem
    segments = segment(upload_path, INTERIM_DIRECTORY / filename)
    downsamples = list(map(downsample, segments))

    response = {'filename': upload_path.name, 'errors': []}

    for frame_paths in downsamples:
        if len(frame_paths) == 0:
            # Happens on rare occasions, for instance Megamind_bugy.avi
            # gets split into 9 segments where the final segment has
            # no length
            continue

        frames = list(map(util.imread, frame_paths))
        keyframe = Keyframe.from_frames(frames)
        video_name = util.video_name_from_path(frame_paths[0])
        segment_id = util.segment_id_from_path(frame_paths[0])

        fpc = FingerprintCollection.from_keyframe(
            keyframe, 
            video_name, 
            segment_id)
        
        fpc = FingerprintCollectionModel.from_fingerprint_collection(fpc)
        try:
            db.session.add(fpc)
            db.session.commit()
        except Exception as e:
            logger.error(e)
            response['errors'].append(e)

    return response


def mark_as_done(future):
    result = future.result()

    name = result['filename']
    if isinstance(result, Exception):
        socketio.emit('state_change', {name: 'ERROR'})
        files[name]['state'] = 'ERROR'
    else:
        socketio.emit('state_change', {name: 'PROCESSED'})
        files[name]['state'] = 'PROCESSED'

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

        future = executor.submit(process_upload, upload_destination)
        future.add_done_callback(mark_as_done)

        return f'Processing {key}'


@app.route('/list')
def list_files():
    return json.dumps(list(files.values()))


if __name__ == '__main__':
    socketio.run(app)
