import boto3
from flask import current_app
from flask.ext.login import AnonymousUserMixin, UserMixin
from itsdangerous import BadSignature, SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


class User(UserMixin, object):

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        self.client = boto3.client('cognito-idp')
        self.email = None
        self.given_name = None,
        self.family_name = None,
        self.session = None
        self.group = 'main'

    def get_id(self):
        """Overriding because Cognito has username instead of an id field. We are using email/username interchangably"""
        return self.email

    def full_name(self):
        return '%s %s' % (self.given_name, self.family_name)

    def is_admin(self):
        return self.member_of_group('administrator')

    def generate_confirmation_token(self, expiration=604800):
        """Generate a confirmation token to email a new user."""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.email})

    def generate_email_change_token(self, new_email, expiration=3600):
        """Generate an email change token to email an existing user."""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.email, 'new_email': new_email})

    def generate_password_reset_token(self, expiration=3600):
        """Generate a password reset change token to email to an existing user."""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.email})

    def confirm_account(self, token):
        """Verify that the provided token is for this user's id."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('confirm') != self.email:
            return False

        self.client.admin_configm_signup(
            UserPoolId=current_app.config['COGNITO_POOL_ID'],
            Username=self.email
        )
        return True

    def reset_password(self, token, previous_password, new_password, access_token):
        """Verify the new password for this user."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('reset') != self.email:
            return False

        self.client.change_password(
            PreviousPassword=previous_password,
            ProposedPassword=new_password,
            AccessToken=access_token
        )
        return True

    def add_to_group(self, group_name):
        """Adds user to a Cognito Group"""
        self.client.admin_add_user_to_group(
            UserPoolId=current_app.config['COGNITO_POOL_ID'],
            Username=self.email,
            GroupName=group_name
        )

    def member_of_group(self, group_name):
        """Returns True if user is a member of the named group"""
        return group_name == self.get_group().get('GroupName')

    def get_group(self):
        """Gets the user's group. It is possible to be in more than one group, but we assume just one group for this demo"""
        response = self.client.admin_list_groups_for_user(
            UserPoolId=current_app.config['COGNITO_POOL_ID'],
            Username=self.email,
        )
        group = response.get('Groups')
        if not group or group == []:
            group = [{'GroupName': 'main', 'Precedence': 0}]
        return group.pop()


    @staticmethod
    def generate_fake(count=100, **kwargs):
        """Generate a number of fake users for testing."""

        # TODO have placebo mock up responses with these 100 users rather than generate them each time
        from random import seed, choice
        from faker import Faker

        fake = Faker()

        seed()
        for i in range(count):
            u = User(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                password=fake.password(),
                confirmed=True,
                role=choice(roles),
                **kwargs)

            u.save()

    def __repr__(self):
        return '<User \'%s\'>' % self.full_name()


class AnonymousUser(AnonymousUserMixin):
    @staticmethod
    def member_of_group(_):
        return False

    @staticmethod
    def is_admin():
        return False
