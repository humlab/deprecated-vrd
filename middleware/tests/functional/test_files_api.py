import json
import os
from pathlib import Path
from typing import Dict

from flask_testing import TestCase

from middleware import create_app
from middleware.models import db
from middleware.models.video_file import VideoFile


def get_json_objs(data_dict):
    return data_dict['files']


class FilesRoutesTest(TestCase):
    def create_app(self):
        os.environ["APP_SETTINGS"] = "middleware.config.TestingConfig"

        app = create_app()

        return app

    def setUp(self):
        # Note: executed inside app.context
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_list_files_empty(self):
        response = self.client.get('/api/files/list')

        # bytes are returned, hence the need to decode
        data = json.loads(response.data.decode())
        files = get_json_objs(data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(files), 0)

    def test_list_files_with_one_video(self):
        file_path = Path('/some/path/to/some_video.avi')
        db.session.add(VideoFile.from_upload(file_path))
        db.session.commit()

        response = self.client.get('/api/files/list')

        # bytes are returned, hence the need to decode
        data = json.loads(response.data.decode())
        files = get_json_objs(data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(files), 1)

        video_name = file_path.name
        video_file = files[0]  # type: Dict[str, str]

        self.assertTrue('video_name' in video_file.keys())
        self.assertEqual(video_file['video_name'], video_name)

    def test_GET_on_upload_should_fail(self):
        response = self.client.get('/api/files/upload')

        self.assertEqual(response.status_code, 405)
