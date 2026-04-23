from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import CustomUser, UserProfile
from apps.events.models import Event, EventMember
from apps.groups.models import Group, Membership
from apps.invites.models import Invite


class InviteFlowTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(username='adm', password='x', email='a@a.com')
        self.member = CustomUser.objects.create_user(username='mem', password='x', email='m@m.com')
        self.guest = CustomUser.objects.create_user(username='gst', password='x', email='g@g.com')
        prof, _ = UserProfile.objects.get_or_create(user=self.guest)
        prof.instruments = ['vocalist']
        prof.save(update_fields=['instruments'])
        self.group = Group.objects.create(name='G1', slug='g1')
        Membership.objects.create(user=self.admin, group=self.group, role='admin')
        Membership.objects.create(user=self.member, group=self.group, role='member')
        self.event = Event.objects.create(
            group=self.group,
            title='Culto',
            date=timezone.now() + timedelta(days=1),
            created_by=self.admin,
        )

    def _token(self, user):
        r = self.client.post('/api/v1/auth/login/', {'username': user.username, 'password': 'x'})
        return r.data['access']

    def test_group_invite_accept_creates_membership(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token(self.admin)}')
        r = self.client.post(
            f'/api/v1/groups/{self.group.slug}/invites/',
            {'invitee_id': self.guest.id, 'role': 'member'},
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        inv_id = r.data['id']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token(self.guest)}')
        r2 = self.client.post(f'/api/v1/invites/{inv_id}/accept/')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertTrue(Membership.objects.filter(user=self.guest, group=self.group).exists())

    def test_event_invite_accept_creates_guest_event_member(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token(self.admin)}')
        r = self.client.post(
            f'/api/v1/groups/{self.group.slug}/events/{self.event.id}/invites/',
            {'invitee_id': self.guest.id, 'instruments': ['vocalist'], 'role_in_event': 'Vocal'},
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        inv_id = r.data['id']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token(self.guest)}')
        r2 = self.client.post(f'/api/v1/invites/{inv_id}/accept/')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        em = EventMember.objects.get(event=self.event, guest_user=self.guest)
        self.assertIsNone(em.membership_id)
        self.assertFalse(Membership.objects.filter(user=self.guest, group=self.group).exists())

    def test_guest_can_get_event_detail(self):
        EventMember.objects.create(
            event=self.event,
            membership=None,
            guest_user=self.guest,
            instruments=['vocalist'],
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token(self.guest)}')
        r = self.client.get(f'/api/v1/groups/{self.group.slug}/events/{self.event.id}/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_pending_count(self):
        Invite.objects.create(
            inviter=self.admin,
            invitee=self.guest,
            kind=Invite.KIND_GROUP,
            group=self.group,
            status=Invite.STATUS_PENDING,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token(self.guest)}')
        r = self.client.get('/api/v1/invites/pending-count/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['count'], 1)
