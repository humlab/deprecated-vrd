from flask_testing import TestCase
import os
import json

from middleware import create_app
from middleware.models import db


class RoutesTest(TestCase):

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

    def testListFilesEmpty(self):
        response = self.client.get('/files/list')

        # bytes are returned, hence the need to decode
        data = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)
