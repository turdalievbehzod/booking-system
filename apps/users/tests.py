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
