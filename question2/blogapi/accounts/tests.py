from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterTests(APITestCase):
    url = reverse('register')

    def test_register_success(self):
        payload = {
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'Sup3rS3cret!pw',
        }
        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'detail': 'Account Created.'})
        self.assertTrue(User.objects.filter(username='alice').exists())
        # Password must be stored hashed, never in plaintext.
        user = User.objects.get(username='alice')
        self.assertTrue(user.check_password('Sup3rS3cret!pw'))
        self.assertNotEqual(user.password, 'Sup3rS3cret!pw')

    def test_register_allows_anonymous(self):
        # No credentials supplied, endpoint must still be reachable.
        response = self.client.post(self.url, {
            'username': 'anon',
            'email': 'anon@example.com',
            'password': 'Sup3rS3cret!pw',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_rejects_weak_password(self):
        # Too short / numeric-only -> validators fire.
        response = self.client.post(self.url, {
            'username': 'bob',
            'email': 'bob@example.com',
            'password': '123',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertFalse(User.objects.filter(username='bob').exists())

    def test_register_rejects_duplicate_username(self):
        User.objects.create_user(username='carol', password='Sup3rS3cret!pw')
        response = self.client.post(self.url, {
            'username': 'carol',
            'email': 'carol2@example.com',
            'password': 'An0therS3cret!pw',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_register_rejects_missing_fields(self):
        response = self.client.post(self.url, {'username': 'dave'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class LoginTests(APITestCase):
    url = reverse('login')

    def setUp(self):
        self.password = 'Sup3rS3cret!pw'
        self.user = User.objects.create_user(
            username='eve', email='eve@example.com', password=self.password)

    def test_login_returns_tokens(self):
        response = self.client.post(self.url, {
            'username': 'eve',
            'password': self.password,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        response = self.client.post(self.url, {
            'username': 'eve',
            'password': 'wrong-password',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_user(self):
        response = self.client.post(self.url, {
            'username': 'nobody',
            'password': self.password,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshTests(APITestCase):
    url = reverse('token_refresh')

    def setUp(self):
        self.user = User.objects.create_user(
            username='frank', password='Sup3rS3cret!pw')
        self.refresh = str(RefreshToken.for_user(self.user))

    def test_refresh_returns_new_access(self):
        response = self.client.post(self.url, {'refresh': self.refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_rejects_invalid_token(self):
        response = self.client.post(self.url, {'refresh': 'not-a-token'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(APITestCase):
    url = reverse('logout')

    def setUp(self):
        self.user = User.objects.create_user(
            username='grace', password='Sup3rS3cret!pw')
        self.refresh = RefreshToken.for_user(self.user)

    def authenticate(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')

    def test_logout_blacklists_refresh_token(self):
        self.authenticate()
        response = self.client.post(self.url, {'refresh': str(self.refresh)})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # A blacklisted refresh token can no longer be exchanged.
        refresh_response = self.client.post(
            reverse('token_refresh'), {'refresh': str(self.refresh)})
        self.assertEqual(refresh_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self):
        response = self.client.post(self.url, {'refresh': str(self.refresh)})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_missing_refresh_token(self):
        self.authenticate()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Refresh token required.'})

    def test_logout_invalid_refresh_token(self):
        self.authenticate()
        response = self.client.post(self.url, {'refresh': 'garbage'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Invalid token.'})


class DeleteAccountTests(APITestCase):
    url = reverse('delete_account')

    def setUp(self):
        self.user = User.objects.create_user(
            username='heidi', password='Sup3rS3cret!pw')

    def authenticate(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_delete_account_success(self):
        self.authenticate()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(username='heidi').exists())

    def test_delete_account_requires_authentication(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(User.objects.filter(username='heidi').exists())
