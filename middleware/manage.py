from flask import current_app
from flask.cli import FlaskGroup
from rq import Connection, Worker

from . import create_app
from .models import db


cli = FlaskGroup(create_app=create_app)


@cli.command('recreate_db')
def recreate_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command('run_extractor')
def run_extractor():
    with Connection(current_app.redis):
        worker = Worker(current_app.extract_queue)
        worker.work()


@cli.command('run_comparator')
def run_comparator():
    with Connection(current_app.redis):
        worker = Worker(current_app.compare_queue)
        worker.work()


if __name__ == '__main__':
    cli()
