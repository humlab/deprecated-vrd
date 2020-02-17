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

__uploads__ = os.getenv('UPLOADS_DIRECTORY', default='static/videos/uploads')
__UPLOAD_DIRECTORY__ = create_directory(__BASE_DIR_PATH__ / __uploads__)

__archive__ = os.getenv('ARCHIVE_DIRECTORY', default='static/videos/archive')
__ARCHIVE_DIRECTORY__ = create_directory(__BASE_DIR_PATH__ / __archive__)

__uploads__ = os.getenv('UPLOADS_FILE')
__UPLOADS_FILE__ = Path(__uploads__) if __uploads__ else None

__archive__ = os.getenv('ARCHIVE_FILE')
__ARCHIVE_FILE__ = Path(__archive__) if __archive__ else None

# TODO: Not part of the application configuration necessarily, move?
INTERIM_DIRECTORY = create_directory(__BASE_DIR_PATH__ / 'interim')


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    UPLOADS_DIRECTORY = __UPLOAD_DIRECTORY__
    ARCHIVE_DIRECTORY = __ARCHIVE_DIRECTORY__
    UPLOADS_FILE = __UPLOADS_FILE__
    ARCHIVE_FILE = __ARCHIVE_FILE__
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')


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
