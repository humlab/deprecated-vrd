import io
import json
import os
from pathlib import Path
from typing import Dict

from flask import url_for
from flask_testing import TestCase

from middleware import create_app
from middleware.models import db
from middleware.models.video_file import VideoFile, VideoFileSchema, VideoFileType


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

    def test_file_info_route_for_file_that_does_not_exist(self):
        response = self.client.get('/api/files/info/doesnotexist.avi')

        # bytes are returned, hence the need to decode
        data = json.loads(response.data.decode())
        fileinfo = data['file']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(fileinfo, {})  # Empty result

    def test_file_info_route(self):
        ARCHIVE_DIRECTORY = self.app.config['ARCHIVE_DIRECTORY']

        # Get any video in the directory,
        video_path = next(
            video for video in ARCHIVE_DIRECTORY.iterdir() if video.suffix == '.mp4'
        )

        # Create our db-object,
        video_file = VideoFile(video_path, VideoFileType.REFERENCE)

        # Add it to the backend so we can fetch it through the api
        db.session.add(video_file)
        db.session.commit()

        response = self.client.get(f'/api/files/info/{video_file.video_name}')

        # bytes are returned, hence the need to decode
        data = json.loads(response.data.decode())
        fileinfo = data['file']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(fileinfo, VideoFileSchema.dump(video_file))

    def test_GET_on_upload_should_fail(self):
        response = self.client.get('/api/files/upload')

        self.assertEqual(response.status_code, 405)

    def test_post_of_query_type_file(self):
        data = {'file_type': 'QUERY'}
        data['file'] = (io.BytesIO(b"abcdef"), 'test.avi')
        response = self.client.post(
            url_for('file.upload_file'), content_type='multipart/form-data', data=data
        )

        self.assertEqual(response.status_code, 202)

        json = response.get_json()
        self.assertEqual(json['file_type'], 'QUERY')
        self.assertEqual(
            json['target_directory'], str(self.app.config['UPLOADS_DIRECTORY'])
        )

    def test_post_of_reference_type_file(self):
        data = {'file_type': 'REFERENCE'}
        data['file'] = (io.BytesIO(b"abcdef"), 'test.avi')
        response = self.client.post(
            url_for('file.upload_file'), content_type='multipart/form-data', data=data
        )

        self.assertEqual(response.status_code, 202)

        json = response.get_json()
        self.assertEqual(json['file_type'], 'REFERENCE')
        self.assertEqual(
            json['target_directory'], str(self.app.config['ARCHIVE_DIRECTORY'])
        )

    def test_post_unknown_file_type(self):
        data = {'file_type': 'UNKNOWN'}
        data['file'] = (io.BytesIO(b"abcdef"), 'test.avi')

        response = self.client.post(
            url_for('file.upload_file'), content_type='multipart/form-data', data=data
        )

        self.assertEqual(response.status_code, 400)

    def test_post_without_a_file(self):
        data = {'file_type': 'QUERY'}

        response = self.client.post(
            url_for('file.upload_file'), content_type='multipart/form-data', data=data
        )

        self.assertEqual(response.status_code, 400)

    def test_reupload_not_allowed(self):
        data = {'file_type': 'QUERY'}
        data['file'] = (io.BytesIO(b"abcdef"), 'test.avi')
        response = self.client.post(
            url_for('file.upload_file'), content_type='multipart/form-data', data=data
        )

        self.assertEqual(response.status_code, 202)

        # This has to be re-done, otherwise a
        #
        # ValueError: I/O operation on closed file.
        #
        # is raised!
        data['file'] = (io.BytesIO(b"abcdef"), 'test.avi')
        response = self.client.post(
            url_for('file.upload_file'), content_type='multipart/form-data', data=data
        )

        self.assertEqual(response.status_code, 403)
