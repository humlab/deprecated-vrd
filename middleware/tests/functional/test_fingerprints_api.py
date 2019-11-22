import os

import sqlalchemy
from flask_testing import TestCase

from middleware import create_app
from middleware.models import db
from middleware.models.fingerprint_comparison import FingerprintComparisonModel


class FingerprintComparisonTest(TestCase):
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

    def test_empty_post(self):
        pass

    def test_comparing_non_existing_video_against_nothing(self):
        response = self.client.post(
            '/fingerprints/compare',
            json=dict(query_video_name='doesnotexist.avi', reference_video_names=[],),
        )

        self.assertTrue(len(response.get_json()) == 0)

    def test_comparing_non_existing_video_against_other_non_existing_videos(self):
        response = self.client.post(
            '/fingerprints/compare',
            json=dict(
                query_video_name='doesnotexist.avi',
                reference_video_names=['neitherdoesthis.avi', 'orthis.avi'],
            ),
        )

        self.assertTrue(len(response.get_json()) == 0)

    def test_comparing_video_against_others_that_do_not_exist(self):
        query_video_name = 'somevideo.avi'

        db.session.add(
            FingerprintComparisonModel(
                query_video_name=query_video_name,
                reference_video_name='someothervideo.avi',
                query_segment_id=1,
                reference_segment_id=1,
                match_level='LEVEL_A',
                similarity_score=1.0,
            )
        )

        db.session.commit()

        response = self.client.post(
            '/fingerprints/compare',
            json=dict(
                query_video_name=query_video_name,
                reference_video_names=['thisdoesnotexist.avi', 'neitherddoesthis.avi'],
            ),
        )

        self.assertTrue(len(response.get_json()) == 0)

    def test_comparing_video_against_another_for_which_there_is_a_comparison(self):
        query_video_name = 'somevideo.avi'
        reference_video_name = 'someothervideo.avi'

        db.session.add(
            FingerprintComparisonModel(
                query_video_name=query_video_name,
                reference_video_name=reference_video_name,
                query_segment_id=1,
                reference_segment_id=1,
                match_level='LEVEL_A',
                similarity_score=1.0,
            )
        )

        db.session.commit()

        response = self.client.post(
            '/fingerprints/compare',
            json=dict(
                query_video_name=query_video_name,
                reference_video_names=[reference_video_name],
            ),
        )

        json_response = response.get_json()

        self.assertTrue(len(json_response) == 1)

        return_values = json_response[0].values()
        self.assertTrue(query_video_name in return_values)
        self.assertTrue(reference_video_name in return_values)

    def test_comparing_video_against_multiple_others(self):
        query_video_name = 'somevideo.avi'
        reference_video_names = ['someothervideo.avi', 'anothervideo.avi']

        for reference_video_name in reference_video_names:
            db.session.add(
                FingerprintComparisonModel(
                    query_video_name=query_video_name,
                    reference_video_name=reference_video_name,
                    query_segment_id=1,
                    reference_segment_id=1,
                    match_level='LEVEL_A',
                    similarity_score=1.0,
                )
            )

            db.session.commit()

        response = self.client.post(
            '/fingerprints/compare',
            json=dict(
                query_video_name=query_video_name,
                reference_video_names=reference_video_names,
            ),
        )

        json_response = response.get_json()
        self.assertTrue(len(json_response) == 2)

        for result in json_response:
            self.assertTrue(query_video_name in result.values())

        response_reference_video_names = [
            d['reference_video_name'] for d in json_response
        ]
        self.assertEqual(reference_video_names, response_reference_video_names)

    def test_unique_constraint(self):
        query_video_name = 'somevideo.avi'
        reference_video_name = 'someothervideo.avi'

        db.session.add(
            FingerprintComparisonModel(
                query_video_name=query_video_name,
                reference_video_name=reference_video_name,
                query_segment_id=1,
                reference_segment_id=1,
                match_level='LEVEL_A',
                similarity_score=1.0,
            )
        )

        db.session.commit()

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            db.session.add(
                FingerprintComparisonModel(
                    query_video_name=query_video_name,
                    reference_video_name=reference_video_name,
                    query_segment_id=1,
                    reference_segment_id=1,
                    match_level='LEVEL_A',
                    similarity_score=0.0,  # Another score
                )
            )

            db.session.commit()
