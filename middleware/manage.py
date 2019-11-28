from flask.cli import FlaskGroup

from . import create_app
from .models import db
from .workers import fingerprint_comparator, fingerprint_extractor


cli = FlaskGroup(create_app=create_app)


@cli.command('recreate_db')
def recreate_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command('run_extractor')
def run_extractor():
    fingerprint_extractor.start()


@cli.command('run_comparator')
def run_comparator():
    fingerprint_comparator.start()


if __name__ == '__main__':
    cli()
