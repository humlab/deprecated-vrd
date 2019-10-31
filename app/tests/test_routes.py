from flask_testing import TestCase
import os
import json

from app import db, create_app


class RoutesTest(TestCase):

    def create_app(self):
        os.environ["APP_SETTINGS"] = "app.config.TestingConfig"
        os.environ["DATABASE_URL"] = "postgres://sid:sid12345@localhost:5432/video_reuse_detector_testing"  # noqa: E501

        return create_app()

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def testListFilesEmpty(self):
        client = self.create_app().test_client()
        response = client.get('/files/list')

        # bytes are returned, hence the need to decode
        data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)
