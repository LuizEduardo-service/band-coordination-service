from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import CustomUser
from apps.groups.models import Group, Membership


class PermissionTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(username='admin', password='pass')
        self.member = CustomUser.objects.create_user(username='member', password='pass')
        self.outsider = CustomUser.objects.create_user(username='outsider', password='pass')

        self.group = Group.objects.create(name='Test Band')
        Membership.objects.create(user=self.admin, group=self.group, role='admin')
        Membership.objects.create(user=self.member, group=self.group, role='member')

    def _get_token(self, user):
        return str(RefreshToken.for_user(user).access_token)

    def test_unauthenticated_get_401(self):
        """No token → 401"""
        resp = self.client.get(f'/api/v1/groups/{self.group.slug}/members/')
        self.assertEqual(resp.status_code, 401)

    def test_member_can_list_members(self):
        """Member → 200"""
        token = self._get_token(self.member)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(f'/api/v1/groups/{self.group.slug}/members/')
        self.assertEqual(resp.status_code, 200)

    def test_outsider_cannot_list_members(self):
        """Outsider (not in group) → 403"""
        token = self._get_token(self.outsider)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(f'/api/v1/groups/{self.group.slug}/members/')
        self.assertEqual(resp.status_code, 403)

    def test_member_cannot_add_member(self):
        """Member tries admin action → 403"""
        token = self._get_token(self.member)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.post(
            f'/api/v1/groups/{self.group.slug}/members/',
            {'user_id': self.outsider.id, 'role': 'member'},
            format='json'
        )
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_add_member(self):
        """Admin can add → 201"""
        token = self._get_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.post(
            f'/api/v1/groups/{self.group.slug}/members/',
            {'user_id': self.outsider.id, 'role': 'member'},
            format='json'
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Membership.objects.filter(user=self.outsider, group=self.group).exists())
