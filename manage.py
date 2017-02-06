#!/usr/bin/env python
import os
import subprocess
import boto3

from flask.ext.script import Manager, Shell

from app import create_app
from app.models import User, EditableHTML, Session as appSession

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


def setup_general(session=None):
    """Runs the set-up needed for both local development and production.
       Also sets up first administrator user."""
    if not session:
        session = boto3.Session()
    client = session.client('cognito-idp')

    # create a pool and print the id
    response = client.create_user_pool(
        PoolName='serverless-flask-test',
        Policies={
            'PasswordPolicy': {
                'MinimumLength': 8,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': True
            }
        },
        AliasAttributes=[
            'email',
        ],
        EmailVerificationMessage='Please use this code to verify your account with Serverless Flask: {####} ',
        EmailVerificationSubject='Email Verification Code for Serverless Flask',
        MfaConfiguration='OFF',
        DeviceConfiguration={
            'ChallengeRequiredOnNewDevice': False,
            'DeviceOnlyRememberedOnUserPrompt': False
        },
        AdminCreateUserConfig={
            'AllowAdminCreateUserOnly': False,
            'UnusedAccountValidityDays': 1,
            'InviteMessageTemplate': {
                'EmailMessage': 'Welcome to this Serverless Flask example.',
                'EmailSubject': 'Serverless Flask Welcomes You.'
            }
        },
        Schema=[
            {
                'Name': 'email',
                'AttributeDataType': 'String',
                'DeveloperOnlyAttribute': False,
                'Mutable': True,
                'Required': True,
            },
            {
                'Name': 'family_name',
                'AttributeDataType': 'String',
                'DeveloperOnlyAttribute': False,
                'Mutable': True,
                'Required': True,
            },
            {
                'Name': 'given_name',
                'AttributeDataType': 'String',
                'DeveloperOnlyAttribute': False,
                'Mutable': True,
                'Required': True,
            },
        ]
    )

    pool_name = response.get('UserPool')['Name']
    print('The cognito user pool {0!s} has been created.'.format(pool_name))
    pool_id = response.get('UserPool')['Id']
    print('The cognito user pool id is {0!s}. Please save this and set it to your environment variable '
          'COGNITO_POOL_ID'.format(pool_id))

    # create an app and print the id
    response = client.create_user_pool_client(
        UserPoolId=pool_id,
        ClientName='Serverless Flask Web App',
        GenerateSecret=False,  # Boto3 doesn't support token auth yet.
        RefreshTokenValidity=30,
        ExplicitAuthFlows=[
            'ADMIN_NO_SRP_AUTH',
        ]
    )

    app_name = response.get('UserPoolClient')['ClientName']
    print('The cognito app {0!s} has been created for your user pool'.format(app_name))
    app_id = response.get('UserPoolClient')['ClientId']
    print('The cognito app id is {0!s}. Please save this and set it to your environment variable '
          'COGNITO_APP_CLIENT_ID'.format(app_id))

    # Create groups in cognito
    client.create_group(
        GroupName='admin',
        UserPoolId=pool_id,
        Description='Administrators',
        Precedence=1
    )

    print('The admin group has been created for the cognito user pool')

    client.create_group(
        GroupName='general',
        UserPoolId=pool_id,
        Description='All Users',
        Precedence=255
    )

    print('The general group has been created for the cognito user pool')

    print('Completed creating Cognito resources')

    # create the dynamo table
    if not EditableHTML.exists():
        EditableHTML.create(read_capacity_units=1, write_capacity_units=1, wait=True)
        print("DynamoDB table for editors created")

    if not appSession.exists():
        appSession.create(read_capacity_units=1, write_capacity_units=1, wait=True)
        print("DynamoDB table for sessions created")


@manager.command
def format():
    """Runs the yapf and isort formatters over the project."""
    isort = 'isort -rc *.py app/'
    yapf = 'yapf -r -i *.py app/'

    print('Running {}'.format(isort))
    subprocess.call(isort, shell=True)

    print('Running {}'.format(yapf))
    subprocess.call(yapf, shell=True)


@manager.command
def upload_static_to_s3():
    """Uploads static content to S3"""
    import flask_s3
    prod_app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    flask_s3.create_all(prod_app)


if __name__ == '__main__':
    manager.run()
