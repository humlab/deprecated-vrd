import redis
from flask.cli import FlaskGroup
from rq import Connection, Worker

from . import create_app
from .config import Config
from .models import db


cli = FlaskGroup(create_app=create_app)


@cli.command('recreate_db')
def recreate_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command('run_extractor')
def run_extractor(with_appcontext=False):
    # TODO: Access app.config['REDIS_URL']
    #
    # See,
    #
    # https://stackoverflow.com/questions/58915590/how-to-access-flask-app-config-from-flaskgroup-when-using-create-app-factory-pat  # noqa: E501
    redis_url = Config.REDIS_URL
    redis_connection = redis.from_url(redis_url)

    with Connection(redis_connection):
        worker = Worker(['extract'])
        worker.work()


@cli.command('run_comparator')
def run_comparator(with_appcontext=False):
    redis_url = Config.REDIS_URL
    redis_connection = redis.from_url(redis_url)

    with Connection(redis_connection):
        worker = Worker(['compare'])
        worker.work()


if __name__ == '__main__':
    cli()
