import time
import unittest
from manage import create_all, drop_all

from app import create_app
from app.models import AnonymousUser, Permission, Role, User


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        create_all()
        Role.insert_roles()

    def tearDown(self):
        drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(email='email', password='password')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='password')
        with self.assertRaises(AttributeError):
            u.password()

    def test_password_verification(self):
        u = User(password='password')
        self.assertTrue(u.verify_password('password'))
        self.assertFalse(u.verify_password('notpassword'))

    def test_password_salts_are_random(self):
        u = User(email='email', password='password')
        u2 = User(email='email', password='password')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self):
        u = User(email='email',password='password')
        u.save()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm_account(token))

    def test_invalid_confirmation_token(self):
        u1 = User(email='email', password='password')
        u2 = User(email='notemail', password='notpassword')
        u1.save()
        u2.save()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm_account(token))

    def test_expired_confirmation_token(self):
        u = User(email='email', password='password')
        u.save()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm_account(token))

    def test_valid_reset_token(self):
        u = User(email='email', password='password')
        u.save()
        token = u.generate_password_reset_token()
        self.assertTrue(u.reset_password(token, 'notpassword'))
        self.assertTrue(u.verify_password('notpassword'))

    def test_invalid_reset_token(self):
        u1 = User(email='email', password='password')
        u2 = User(email='notemail', password='notpassword')
        u1.save()
        u2.save()
        token = u1.generate_password_reset_token()
        self.assertFalse(u2.reset_password(token, 'notnotpassword'))
        self.assertTrue(u2.verify_password('notpassword'))

    def test_valid_email_change_token(self):
        u = User(email='user@example.com', password='password')
        u.save()
        token = u.generate_email_change_token('otheruser@example.org')
        self.assertTrue(u.change_email(token))
        self.assertTrue(u.email == 'otheruser@example.org')

    def test_invalid_email_change_token(self):
        u1 = User(email='user@example.com', password='password')
        u2 = User(email='otheruser@example.org', password='notpassword')
        u1.save()
        u2.save()
        token = u1.generate_email_change_token('otherotheruser@example.net')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 'otheruser@example.org')

    def test_duplicate_email_change_token(self):
        u1 = User(email='user@example.com', password='password')
        u2 = User(email='otheruser@example.org', password='notpassword')
        r = u2.role
        import json
        json.dumps(r)
        u1.save()
        u2.save()
        token = u2.generate_email_change_token('user@example.com')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 'otheruser@example.org')

    def test_roles_and_permissions(self):
        Role.insert_roles()
        u = User(email='user@example.com', password='password')
        self.assertTrue(u.can(Permission.GENERAL))
        self.assertFalse(u.can(Permission.ADMINISTER))

    def test_make_administrator(self):
        Role.insert_roles()
        u = User(email='user@example.com', password='password')
        self.assertFalse(u.can(Permission.ADMINISTER))
        u.role = Role.get('Administrator')
        self.assertTrue(u.can(Permission.ADMINISTER))

    def test_administrator(self):
        Role.insert_roles()
        r = Role.get('Administrator')
        u = User(email='user@example.com', password='password', role=r)
        self.assertTrue(u.can(Permission.ADMINISTER))
        self.assertTrue(u.can(Permission.GENERAL))
        self.assertTrue(u.is_admin())

    def test_anonymous(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.GENERAL))
