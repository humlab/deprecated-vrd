import json
import os

from flask_testing import TestCase

from middleware import create_app
from middleware.models import db


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

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

    def test_get_on_upload(self):
        response = self.client.get('/api/files/upload')

        self.assertEqual(response.status_code, 405)
