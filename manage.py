#!/usr/bin/env python
import os
import subprocess

from flask.ext.script import Manager, Shell

from app import create_app
from app.models import User, EditableHTML

if os.path.exists('.env'):
    print('Importing environment from .env file')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
# migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, User=User)


manager.add_command('shell', Shell(make_context=make_shell_context))
# manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


def drop_all():
    if EditableHTML.exists():
        EditableHTML.delete_table()


def create_all():
    if not EditableHTML.exists():
        EditableHTML.create_table(wait=True)


@manager.command
def recreate_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    drop_all()
    create_all()


@manager.option(
    '-n',
    '--number-users',
    default=10,
    type=int,
    help='Number of each model type to create',
    dest='number_users')
def add_fake_data(number_users):
    """
    Adds fake data to the database.
    """
    User.generate_fake(count=number_users)


@manager.command
def setup_dev():
    """Runs the set-up needed for local development."""
    setup_general()


@manager.command
def setup_prod():
    """Runs the set-up needed for production."""
    setup_general()


def setup_general():
    """Runs the set-up needed for both local development and production.
       Also sets up first administrator user."""

    # create a pool and print the id
    # create an app and print the id
    # Create groups in cognito
    # create administrator

    # create the dynamo table
    # add the about page to the dynamo table

    pass


@manager.command
def format():
    """Runs the yapf and isort formatters over the project."""
    isort = 'isort -rc *.py app/'
    yapf = 'yapf -r -i *.py app/'

    print('Running {}'.format(isort))
    subprocess.call(isort, shell=True)

    print('Running {}'.format(yapf))
    subprocess.call(yapf, shell=True)


if __name__ == '__main__':
    manager.run()
