import boto3
from flask import current_app, session

from app.models import User, AnonymousUser
from . import login_manager

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def user_loader(email):
    return get_user(email)


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    password = request.form.get('password')
    if email and password:
        return authenticate_user(username=email, password=password)


def list_groups(boto3_session=None):
    if not boto3_session:
        boto3_session = boto3.Session()

    client = boto3_session.client('cognito-idp')
    response = client.list_groups(
        UserPoolId=current_app.config['COGNITO_POOL_ID']
    )
    return response.get('Groups', [])


def list_users(boto3_session=None):
    if not boto3_session:
        boto3_session = boto3.Session()

    client = boto3_session.client('cognito-idp')
    response = client.list_users(
        UserPoolId=current_app.config['COGNITO_POOL_ID']
    )
    return response.get('Users', [])


def get_user(email, boto3_session=None):
    if not boto3_session:
        boto3_session = boto3.Session()

    client = boto3_session.client('cognito-idp')
    try:
        response = client.admin_get_user(
            UserPoolId=current_app.config['COGNITO_POOL_ID'],
            Username=email
        )
    except Exception:
        # Ideally the exception UserNotFoundException would be specified, but it is declared in a json within botocore.
        return

    user = User()
    user.enabled = response.get('Enabled', False)
    for attribute in response.get('UserAttributes'):
        setattr(user, attribute[u'Name'], attribute[u'Value'])

    user.group = user.get_group()

    return user


def authenticate_user(username, password, boto3_session=None):
    if not boto3_session:
        boto3_session = boto3.Session()

    client = boto3_session.client('cognito-idp')
    try:
        response = client.admin_initiate_auth(
            UserPoolId=current_app.config['COGNITO_POOL_ID'],
            ClientId=current_app.config['COGNITO_APP_CLIENT_ID'],
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={'USERNAME': username,
                            'PASSWORD': password})
    except Exception as m:
        print m.message
        # Ideally the exception UserNotFoundException would be specified, but it is declared in a json within botocore.
        return

    session['expires_in'] = response['AuthenticationResult']['ExpiresIn']
    session['id_token'] = response['AuthenticationResult']['IdToken']
    session['refresh_token'] = response['AuthenticationResult']['RefreshToken']
    session['access_token'] = response['AuthenticationResult']['AccessToken']
    session['token_type'] = response['AuthenticationResult']['TokenType']

    return get_user(email=username)


def user_exists(email, boto3_session=None):
    """Returns True if the user exists"""
    if not boto3_session:
        boto3_session = boto3.Session()

    client = boto3_session.client('cognito-idp')
    response = client.list_users(
        UserPoolId=current_app.config['COGNITO_POOL_ID'],
        AttributesToGet=['email'],
        Limit=1,
        Filter='email = \"{0!s}\"'.format(email)
    )
    if len(response.get('Users', [])) > 0:
        return True
    return False
