import os

from flask_testing import TestCase

from middleware import create_app


class ConfigTest(TestCase):
    def create_app(self):
        return create_app()

    def test_development_config(self):
        self.app.config.from_object('middleware.config.DevelopmentConfig')
        self.assertFalse(self.app.config['TESTING'])

        self.assertEqual(
            self.app.config['SQLALCHEMY_DATABASE_URI'], os.environ.get('DATABASE_URL')
        )

    def test_testing_config(self):
        self.app.config.from_object('middleware.config.TestingConfig')
        self.assertTrue(self.app.config['TESTING'])

        self.assertEqual(
            self.app.config['SQLALCHEMY_DATABASE_URI'],
            os.environ.get('DATABASE_TEST_URL'),
        )
