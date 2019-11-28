import os
from pathlib import Path


# TODO: Migrate to services.__init__.py when uploading passes a file reference
# directly to the service
def create_directory(path: Path):
    if not path.exists():
        path.mkdir()

    return path


__BASE_DIR__ = os.path.dirname(os.path.dirname(__file__))
__BASE_DIR_PATH__ = Path(__BASE_DIR__)

__uploads__ = os.getenv('UPLOADS', default='uploads')
__UPLOAD_DIRECTORY__ = create_directory(__BASE_DIR_PATH__ / __uploads__)

__archive__ = os.getenv('REFERENCE_ARCHIVE', default='archive')
__ARCHIVE_DIRECTORY__ = create_directory(__BASE_DIR_PATH__ / __archive__)

# TODO: Not part of the application configuration necessarily, move?
INTERIM_DIRECTORY = create_directory(__BASE_DIR_PATH__ / 'interim')


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    QUEUES = ['extract', 'compare']
    UPLOAD_DIRECTORY = __UPLOAD_DIRECTORY__
    ARCHIVE_DIRECTORY = __ARCHIVE_DIRECTORY__


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_TEST_URL']
