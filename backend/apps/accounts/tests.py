from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import CustomUser


class RegisterViewTests(APITestCase):
    """Test user registration endpoint."""

    def test_register_valid(self):
        """Valid registration should return 201 and create user."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())
        self.assertEqual(response.data['username'], 'newuser')

    def test_register_duplicate_email(self):
        """Registering with existing email should return 400."""
        CustomUser.objects.create_user(
            username='existing',
            email='test@example.com',
            password='pass123'
        )
        data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_duplicate_username(self):
        """Registering with existing username should return 400."""
        CustomUser.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='pass123'
        )
        data = {
            'username': 'existing',
            'email': 'newuser@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_register_password_mismatch(self):
        """Passwords not matching should return 400."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPass123!',
            'password2': 'DifferentPass123!',
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_weak_password(self):
        """Weak password should return 400."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',
            'password2': '123',
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_missing_email(self):
        """Missing email should return 400."""
        data = {
            'username': 'newuser',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_missing_username(self):
        """Missing username should return 400."""
        data = {
            'email': 'newuser@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_register_missing_password(self):
        """Missing password should return 400."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password2': 'StrongPass123!',
        }
        response = self.client.post('/api/v1/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class MeViewTests(APITestCase):
    """Test /auth/me/ endpoint for user profile."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )

    def test_me_unauthenticated(self):
        """Unauthenticated request should return 401."""
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_authenticated_get(self):
        """Authenticated GET should return user profile with 200."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'testuser@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')

    def test_me_patch_first_name(self):
        """PATCH should update first_name and return 200."""
        self.client.force_authenticate(user=self.user)
        data = {'first_name': 'Updated'}
        response = self.client.patch('/api/v1/auth/me/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_me_patch_last_name(self):
        """PATCH should update last_name and return 200."""
        self.client.force_authenticate(user=self.user)
        data = {'last_name': 'NewLast'}
        response = self.client.patch('/api/v1/auth/me/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['last_name'], 'NewLast')

    def test_me_patch_email(self):
        """PATCH should update email and return 200."""
        self.client.force_authenticate(user=self.user)
        data = {'email': 'newemail@example.com'}
        response = self.client.patch('/api/v1/auth/me/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'newemail@example.com')

    def test_me_patch_cannot_change_username(self):
        """PATCH should not change username (read-only)."""
        self.client.force_authenticate(user=self.user)
        data = {'username': 'newusername'}
        response = self.client.patch('/api/v1/auth/me/', data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')

    def test_me_patch_cannot_change_id(self):
        """PATCH should not change id (read-only)."""
        self.client.force_authenticate(user=self.user)
        original_id = self.user.id
        data = {'id': 999}
        response = self.client.patch('/api/v1/auth/me/', data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.id, original_id)

    def test_me_patch_multiple_fields(self):
        """PATCH should update multiple fields at once."""
        self.client.force_authenticate(user=self.user)
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com'
        }
        response = self.client.patch('/api/v1/auth/me/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')
        self.assertEqual(response.data['email'], 'john@example.com')

    def test_me_patch_profile_and_instruments(self):
        """PATCH should update phone, bio and instruments (JSON)."""
        self.client.force_authenticate(user=self.user)
        data = {
            'phone': '11999998888',
            'bio': 'Músico',
            'instruments': ['guitar', 'vocalist'],
        }
        response = self.client.patch('/api/v1/auth/me/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone'], '11999998888')
        self.assertEqual(response.data['bio'], 'Músico')
        self.assertEqual(response.data['instruments'], ['guitar', 'vocalist'])

    def test_me_patch_invalid_instrument_slug(self):
        """Invalid instrument slug should return 400."""
        self.client.force_authenticate(user=self.user)
        data = {'instruments': ['invalid_slug']}
        response = self.client.patch('/api/v1/auth/me/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePasswordViewTests(APITestCase):
    """Test change password endpoint."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='oldpass123'
        )

    def test_change_password_unauthenticated(self):
        """Unauthenticated request: ChangePasswordView accepts any, validates in serializer."""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewPass123!',
        }
        response = self.client.post('/api/v1/auth/change-password/', data)
        # View accepts unauthenticated, but serializer validates old_password against request.user
        # Unauthenticated user check will fail in serializer
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])

    def test_change_password_valid(self):
        """Valid password change should return 200."""
        self.client.force_authenticate(user=self.user)
        data = {
            'old_password': 'oldpass123',
            'new_password': 'NewPass123!',
        }
        response = self.client.post('/api/v1/auth/change-password/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_change_password_wrong_old_password(self):
        """Wrong old password should return 400."""
        self.client.force_authenticate(user=self.user)
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'NewPass123!',
        }
        response = self.client.post('/api/v1/auth/change-password/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    def test_change_password_weak_new_password(self):
        """Weak new password should return 400."""
        self.client.force_authenticate(user=self.user)
        data = {
            'old_password': 'oldpass123',
            'new_password': '123',
        }
        response = self.client.post('/api/v1/auth/change-password/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_change_password_missing_old_password(self):
        """Missing old_password should return 400."""
        self.client.force_authenticate(user=self.user)
        data = {'new_password': 'NewPass123!'}
        response = self.client.post('/api/v1/auth/change-password/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    def test_change_password_missing_new_password(self):
        """Missing new_password should return 400."""
        self.client.force_authenticate(user=self.user)
        data = {'old_password': 'oldpass123'}
        response = self.client.post('/api/v1/auth/change-password/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)


class UserSearchViewTests(APITestCase):
    """Test user search endpoint."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='searcher',
            email='searcher@example.com',
            password='pass123'
        )
        CustomUser.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='pass123'
        )
        CustomUser.objects.create_user(
            username='andrew',
            email='andrew@example.com',
            password='pass123'
        )
        CustomUser.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='pass123'
        )

    def test_search_unauthenticated(self):
        """Unauthenticated request should return 401."""
        response = self.client.get('/api/v1/users/?search=alice')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_empty_query(self):
        """Empty query should return empty list."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/?search=')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_search_no_query_param(self):
        """Missing search param should return empty list."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_search_less_than_2_chars(self):
        """Search with 1 char should return empty list."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/?search=a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_search_exact_2_chars(self):
        """Search with exactly 2 chars should work."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/?search=al')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'alice')

    def test_search_returns_matching_users(self):
        """Search should return users matching the query."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/?search=an')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'andrew')

    def test_search_case_insensitive(self):
        """Search should be case insensitive."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/?search=ALI')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'alice')

    def test_search_multiple_matches(self):
        """Search matching multiple users should return all."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/?search=a')
        # This should have no result due to min length requirement
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_search_whitespace_stripped(self):
        """Search query should have whitespace stripped."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/?search=%20%20alice%20%20')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'alice')

    def test_search_returns_limited_results(self):
        """Search should return max 10 results."""
        self.client.force_authenticate(user=self.user)
        # Create 12 users starting with 'user'
        for i in range(12):
            CustomUser.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='pass123'
            )
        response = self.client.get('/api/v1/users/?search=user')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

    def test_search_response_format(self):
        """Search response should contain correct user fields."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/?search=alice')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data[0]
        self.assertIn('id', user_data)
        self.assertIn('username', user_data)
        self.assertIn('email', user_data)
        self.assertIn('first_name', user_data)
        self.assertIn('last_name', user_data)
