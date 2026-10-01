import os
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.users.models import User


class AuthApiTests(APITestCase):
    def test_register_login_me(self):
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'alice', 'email': 'Alice@Example.com', 'password': 'strong-pass-123', 'role': 'admin',
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(username='alice')
        self.assertEqual(user.role, User.Role.CUSTOMER)  # role can't be self-assigned
        self.assertEqual(user.email, 'alice@example.com')
        self.assertNotEqual(user.password, 'strong-pass-123')  # stored hashed

        response = self.client.post('/api/v1/auth/login/', {'username': 'alice', 'password': 'strong-pass-123'})
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'alice')

    def test_weak_password_and_duplicate_email(self):
        User.objects.create_user('bob', 'bob@example.com', 'pass-12345')
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'bob2', 'email': 'BOB@example.com', 'password': '123',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get('/api/v1/auth/me/').status_code, 401)


ADMIN_ENV = {
    'DJANGO_SUPERUSER_USERNAME': 'boss',
    'DJANGO_SUPERUSER_EMAIL': 'Boss@Example.com',
    'DJANGO_SUPERUSER_PASSWORD': 'strong-pass-123',
}


class EnsureSuperuserCommandTests(TestCase):
    def run_command(self, env=ADMIN_ENV):
        out, err = StringIO(), StringIO()
        with mock.patch.dict(os.environ, env, clear=False):
            call_command('ensure_superuser', stdout=out, stderr=err)
        return out.getvalue() + err.getvalue()

    def test_creates_admin_once(self):
        self.assertIn('created', self.run_command())
        user = User.objects.get(username='boss')
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertEqual(user.email, 'boss@example.com')
        self.assertIn('already exists', self.run_command())  # idempotent on restart

    def test_email_used_by_customer_is_reported(self):
        User.objects.create_user('customer', 'boss@example.com', 'pass-12345')
        self.assertIn('already used', self.run_command())
        self.assertFalse(User.objects.filter(username='boss').exists())

    def test_never_promotes_existing_customer(self):
        # Anyone can register the admin's username first; that must not make them admin.
        User.objects.create_user('boss', 'someone@example.com', 'pass-12345')
        self.assertIn('regular account', self.run_command())
        self.assertFalse(User.objects.get(username='boss').is_superuser)

    def test_skips_when_not_configured(self):
        env = {**ADMIN_ENV, 'DJANGO_SUPERUSER_PASSWORD': ''}
        self.assertIn('skipped', self.run_command(env))
        self.assertFalse(User.objects.exists())
