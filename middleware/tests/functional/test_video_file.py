import os
from pathlib import Path

import sqlalchemy
from flask_testing import TestCase

from middleware import create_app
from middleware.models import db
from middleware.models.video_file import VideoFile


class VideoFileTest(TestCase):
    def create_app(self):
        os.environ["APP_SETTINGS"] = "middleware.config.TestingConfig"

        app = create_app()

        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_unique_constraint(self):
        file_path = Path('/some/path/to/some/video.avi')

        # Create an instance of the video file in the database
        db.session.add(VideoFile(file_path))

        db.session.commit()

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            # Adding the same video back shouldn't be possible
            db.session.add(VideoFile(file_path))

            db.session.commit()
