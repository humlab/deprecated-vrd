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


@cli.command('run_worker')
def run_worker():
    # TODO: Access app.config['REDIS_URL']
    #
    # See,
    #
    # https://stackoverflow.com/questions/58915590/how-to-access-flask-app-config-from-flaskgroup-when-using-create-app-factory-pat  # noqa: E501
    redis_url = Config.REDIS_URL
    redis_connection = redis.from_url(redis_url)

    with Connection(redis_connection):
        worker = Worker(Config.QUEUES)
        worker.work()


if __name__ == '__main__':
    cli()
