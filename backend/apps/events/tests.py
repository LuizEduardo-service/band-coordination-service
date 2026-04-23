from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, timedelta
from apps.accounts.models import CustomUser
from apps.groups.models import Group, Membership
from apps.events.models import Event, EventMember, Song, EventSong, SongSuggestion


class EventListViewTests(APITestCase):
    """Test event list and creation endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )
        self.member_user = CustomUser.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        self.outsider_user = CustomUser.objects.create_user(
            username='outsider',
            email='outsider@example.com',
            password='pass123'
        )
        self.group = Group.objects.create(name='Test Group', slug='test-group')
        Membership.objects.create(user=self.admin_user, group=self.group, role='admin')
        Membership.objects.create(user=self.member_user, group=self.group, role='member')
        self.event = Event.objects.create(
            group=self.group,
            title='Test Event',
            date=datetime.now() + timedelta(days=1),
            created_by=self.admin_user
        )

    def test_list_unauthenticated(self):
        """Unauthenticated request should return 401."""
        response = self.client.get('/api/v1/groups/test-group/events/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_member_can_list(self):
        """Group member should see events (200)."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get('/api/v1/groups/test-group/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Event')

    def test_list_outsider_cannot_list(self):
        """Non-group member should get 404."""
        self.client.force_authenticate(user=self.outsider_user)
        response = self.client.get('/api/v1/groups/test-group/events/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_nonexistent_group(self):
        """Accessing non-existent group should return 404."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get('/groups/nonexistent/events/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_admin_can_create(self):
        """Admin should create event (201)."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'title': 'New Event',
            'date': (datetime.now() + timedelta(days=2)).isoformat(),
            'description': 'Test description'
        }
        response = self.client.post('/api/v1/groups/test-group/events/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Event')
        self.assertTrue(Event.objects.filter(title='New Event').exists())

    def test_create_member_cannot_create(self):
        """Non-admin member should get 403."""
        self.client.force_authenticate(user=self.member_user)
        data = {
            'title': 'New Event',
            'date': (datetime.now() + timedelta(days=2)).isoformat(),
        }
        response = self.client.post('/api/v1/groups/test-group/events/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_outsider_cannot_create(self):
        """Outsider should get 403."""
        self.client.force_authenticate(user=self.outsider_user)
        data = {
            'title': 'New Event',
            'date': (datetime.now() + timedelta(days=2)).isoformat(),
        }
        response = self.client.post('/api/v1/groups/test-group/events/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_missing_title(self):
        """Create without title should return 400."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'date': (datetime.now() + timedelta(days=2)).isoformat()}
        response = self.client.post('/api/v1/groups/test-group/events/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_create_missing_date(self):
        """Create without date should return 400."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'title': 'New Event'}
        response = self.client.post('/api/v1/groups/test-group/events/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', response.data)

    def test_list_filters_upcoming(self):
        """Filtering upcoming=true should return only future events."""
        Event.objects.create(
            group=self.group,
            title='Past Event',
            date=datetime.now() - timedelta(days=2),
            created_by=self.admin_user
        )
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get('/api/v1/groups/test-group/events/?upcoming=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(item['is_upcoming'] for item in response.data))

    def test_list_invalid_ordering_returns_400(self):
        """Invalid ordering query should return 400."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get('/api/v1/groups/test-group/events/?ordering=invalid_field')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ordering', response.data)


class EventDetailViewTests(APITestCase):
    """Test event detail, update, and delete endpoints."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )
        self.member_user = CustomUser.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        self.outsider_user = CustomUser.objects.create_user(
            username='outsider',
            email='outsider@example.com',
            password='pass123'
        )
        self.group = Group.objects.create(name='Test Group', slug='test-group')
        Membership.objects.create(user=self.admin_user, group=self.group, role='admin')
        Membership.objects.create(user=self.member_user, group=self.group, role='member')
        self.event = Event.objects.create(
            group=self.group,
            title='Test Event',
            date=datetime.now() + timedelta(days=1),
            description='Original description',
            created_by=self.admin_user
        )

    def test_detail_unauthenticated(self):
        """Unauthenticated request should return 401."""
        response = self.client.get(f'/api/v1/groups/test-group/events/{self.event.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_member_can_get(self):
        """Member should view event detail (200)."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(f'/api/v1/groups/test-group/events/{self.event.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Event')

    def test_detail_outsider_cannot_get(self):
        """Outsider should get 404."""
        self.client.force_authenticate(user=self.outsider_user)
        response = self.client.get(f'/api/v1/groups/test-group/events/{self.event.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_nonexistent_event(self):
        """Accessing non-existent event should return 404."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get('/api/v1/groups/test-group/events/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_admin_can_update(self):
        """Admin should update event (200)."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'title': 'Updated Event', 'description': 'New description'}
        response = self.client.patch(f'/api/v1/groups/test-group/events/{self.event.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'Updated Event')

    def test_patch_member_cannot_update(self):
        """Non-admin should get 403."""
        self.client.force_authenticate(user=self.member_user)
        data = {'title': 'Updated Event'}
        response = self.client.patch(f'/api/v1/groups/test-group/events/{self.event.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_admin_can_delete(self):
        """Admin should delete event (204)."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/v1/groups/test-group/events/{self.event.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_delete_member_cannot_delete(self):
        """Non-admin should get 403."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(f'/api/v1/groups/test-group/events/{self.event.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EventMemberListViewTests(APITestCase):
    """Test event member addition."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )
        self.member_user = CustomUser.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        self.user_to_add = CustomUser.objects.create_user(
            username='toadd',
            email='toadd@example.com',
            password='pass123'
        )
        self.outsider_user = CustomUser.objects.create_user(
            username='outsider',
            email='outsider@example.com',
            password='pass123'
        )
        self.group = Group.objects.create(name='Test Group', slug='test-group')
        self.group2 = Group.objects.create(name='Other Group', slug='other-group')
        self.admin_membership = Membership.objects.create(
            user=self.admin_user, group=self.group, role='admin'
        )
        self.member_membership = Membership.objects.create(
            user=self.member_user, group=self.group, role='member'
        )
        self.user_to_add_membership = Membership.objects.create(
            user=self.user_to_add, group=self.group, role='member'
        )
        self.outsider_membership = Membership.objects.create(
            user=self.outsider_user, group=self.group2, role='member'
        )
        self.user_to_add.profile.instruments = ['guitar', 'bass']
        self.user_to_add.profile.save(update_fields=['instruments'])
        self.outsider_user.profile.instruments = ['keyboard']
        self.outsider_user.profile.save(update_fields=['instruments'])
        self.event = Event.objects.create(
            group=self.group,
            title='Test Event',
            date=datetime.now() + timedelta(days=1),
            created_by=self.admin_user
        )

    def test_add_member_unauthenticated(self):
        """Unauthenticated request should return 401."""
        data = {'membership_id': self.user_to_add_membership.id, 'instruments': ['guitar']}
        response = self.client.post(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_member_admin_can_add(self):
        """Admin should add member to event (201)."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'membership_id': self.user_to_add_membership.id, 'instruments': ['guitar']}
        response = self.client.post(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            EventMember.objects.filter(
                event=self.event,
                membership=self.user_to_add_membership
            ).exists()
        )

    def test_add_member_member_cannot_add(self):
        """Non-admin should get 403."""
        self.client.force_authenticate(user=self.member_user)
        data = {'membership_id': self.user_to_add_membership.id, 'instruments': ['guitar']}
        response = self.client.post(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_member_invalid_membership_id(self):
        """Invalid membership_id should return 400."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'membership_id': 99999, 'instruments': ['guitar']}
        response = self.client.post(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_member_from_another_group(self):
        """Adding member from different group should return 400."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'membership_id': self.outsider_membership.id, 'instruments': ['keyboard']}
        response = self.client.post(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_member_duplicate(self):
        """Adding same member twice should return 400."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'membership_id': self.user_to_add_membership.id, 'instruments': ['guitar']}
        self.client.post(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/', data, format='json'
        )
        response = self.client.post(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_members_member_can_get(self):
        """Group member should list event members (200)."""
        EventMember.objects.create(
            event=self.event,
            membership=self.user_to_add_membership,
            instruments=['guitar'],
        )
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(f'/api/v1/groups/test-group/events/{self.event.id}/members/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_add_member_instrument_not_on_user_profile(self):
        """Instrument not in user profile should return 400."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'membership_id': self.user_to_add_membership.id, 'instruments': ['keyboard']}
        response = self.client.post(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_member_user_without_profile_instruments(self):
        """User with empty instruments profile should return 400."""
        empty_user = CustomUser.objects.create_user(
            username='noinst', email='noinst@example.com', password='pass123'
        )
        m = Membership.objects.create(user=empty_user, group=self.group, role='member')
        self.client.force_authenticate(user=self.admin_user)
        data = {'membership_id': m.id, 'instruments': ['guitar']}
        response = self.client.post(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/', data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EventMemberDetailViewTests(APITestCase):
    """Test event member removal."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )
        self.member_user = CustomUser.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        self.group = Group.objects.create(name='Test Group', slug='test-group')
        self.admin_membership = Membership.objects.create(
            user=self.admin_user, group=self.group, role='admin'
        )
        self.member_membership = Membership.objects.create(
            user=self.member_user, group=self.group, role='member'
        )
        self.member_user.profile.instruments = ['guitar', 'drums']
        self.member_user.profile.save(update_fields=['instruments'])
        self.event = Event.objects.create(
            group=self.group,
            title='Test Event',
            date=datetime.now() + timedelta(days=1),
            created_by=self.admin_user
        )
        self.event_member = EventMember.objects.create(
            event=self.event,
            membership=self.member_membership,
            instruments=['guitar'],
        )

    def test_remove_member_unauthenticated(self):
        """Unauthenticated request should return 401."""
        response = self.client.delete(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remove_member_admin_can_remove(self):
        """Admin should remove member (204)."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EventMember.objects.filter(id=self.event_member.id).exists())

    def test_remove_member_non_admin_cannot_remove(self):
        """Non-admin should get 403."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_member_nonexistent(self):
        """Removing non-existent member should return 404."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/99999/'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_member_role_admin_can_update(self):
        """Admin should update role_in_event (200)."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'role_in_event': 'guitarra base'}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member.id}/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event_member.refresh_from_db()
        self.assertEqual(self.event_member.role_in_event, 'guitarra base')

    def test_patch_member_role_non_admin_cannot_update(self):
        """Non-admin should not update role_in_event."""
        self.client.force_authenticate(user=self.member_user)
        data = {'role_in_event': 'teclado'}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member.id}/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ParticipationViewTests(APITestCase):
    """Test participation status update."""

    def setUp(self):
        """Set up test data."""
        self.user1 = CustomUser.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = CustomUser.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.group = Group.objects.create(name='Test Group', slug='test-group')
        self.membership1 = Membership.objects.create(
            user=self.user1, group=self.group, role='member'
        )
        self.membership2 = Membership.objects.create(
            user=self.user2, group=self.group, role='member'
        )
        self.user1.profile.instruments = ['vocalist']
        self.user1.profile.save(update_fields=['instruments'])
        self.user2.profile.instruments = ['bass']
        self.user2.profile.save(update_fields=['instruments'])
        self.event = Event.objects.create(
            group=self.group,
            title='Test Event',
            date=datetime.now() + timedelta(days=1),
            created_by=self.user1
        )
        self.event_member1 = EventMember.objects.create(
            event=self.event,
            membership=self.membership1,
            participation='pending',
            instruments=['vocalist'],
        )
        self.event_member2 = EventMember.objects.create(
            event=self.event,
            membership=self.membership2,
            participation='pending',
            instruments=['bass'],
        )

    def test_update_own_participation_unauthenticated(self):
        """Unauthenticated request should return 401."""
        data = {'participation': 'confirmed'}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member1.id}/participation/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_own_participation_to_confirmed(self):
        """User should update own participation to confirmed (200)."""
        self.client.force_authenticate(user=self.user1)
        data = {'participation': 'confirmed'}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member1.id}/participation/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event_member1.refresh_from_db()
        self.assertEqual(self.event_member1.participation, 'confirmed')

    def test_update_own_participation_to_declined(self):
        """User should update own participation to declined (200)."""
        self.client.force_authenticate(user=self.user1)
        data = {'participation': 'declined'}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member1.id}/participation/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event_member1.refresh_from_db()
        self.assertEqual(self.event_member1.participation, 'declined')

    def test_update_own_participation_to_pending(self):
        """User should update own participation back to pending (200)."""
        self.event_member1.participation = 'confirmed'
        self.event_member1.save()
        self.client.force_authenticate(user=self.user1)
        data = {'participation': 'pending'}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member1.id}/participation/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_other_participation_fails(self):
        """User cannot update another's participation (404)."""
        self.client.force_authenticate(user=self.user1)
        data = {'participation': 'confirmed'}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member2.id}/participation/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_participation_invalid_value(self):
        """Invalid participation value should return 400."""
        self.client.force_authenticate(user=self.user1)
        data = {'participation': 'invalid'}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member1.id}/participation/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_participation_missing_field(self):
        """Missing participation field should return 400."""
        self.client.force_authenticate(user=self.user1)
        data = {}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/members/{self.event_member1.id}/participation/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SongListViewTests(APITestCase):
    """Test song list and creation."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )
        self.member_user = CustomUser.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        self.outsider_user = CustomUser.objects.create_user(
            username='outsider',
            email='outsider@example.com',
            password='pass123'
        )
        self.group = Group.objects.create(name='Test Group', slug='test-group')
        Membership.objects.create(user=self.admin_user, group=self.group, role='admin')
        Membership.objects.create(user=self.member_user, group=self.group, role='member')
        self.song = Song.objects.create(
            group=self.group,
            title='Test Song',
            artist='Test Artist',
            key='C'
        )

    def test_list_unauthenticated(self):
        """Unauthenticated request should return 401."""
        response = self.client.get('/api/v1/groups/test-group/songs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_member_can_list(self):
        """Member should list songs (200)."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get('/api/v1/groups/test-group/songs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Song')

    def test_list_outsider_cannot_list(self):
        """Outsider should get 403."""
        self.client.force_authenticate(user=self.outsider_user)
        response = self.client.get('/api/v1/groups/test-group/songs/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_admin_can_create(self):
        """Admin should create song (201)."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'title': 'New Song',
            'artist': 'New Artist',
            'key': 'D'
        }
        response = self.client.post('/api/v1/groups/test-group/songs/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Song.objects.filter(title='New Song').exists())

    def test_create_member_cannot_create(self):
        """Member should get 403."""
        self.client.force_authenticate(user=self.member_user)
        data = {
            'title': 'New Song',
            'artist': 'New Artist'
        }
        response = self.client.post('/api/v1/groups/test-group/songs/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_outsider_cannot_create(self):
        """Outsider should get 403."""
        self.client.force_authenticate(user=self.outsider_user)
        data = {
            'title': 'New Song',
            'artist': 'New Artist'
        }
        response = self.client.post('/api/v1/groups/test-group/songs/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_missing_title(self):
        """Create without title should return 400."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'artist': 'New Artist'}
        response = self.client.post('/api/v1/groups/test-group/songs/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)


class SongDetailViewTests(APITestCase):
    """Test song detail, update, and delete."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )
        self.member_user = CustomUser.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        self.outsider_user = CustomUser.objects.create_user(
            username='outsider',
            email='outsider@example.com',
            password='pass123'
        )
        self.group = Group.objects.create(name='Test Group', slug='test-group')
        Membership.objects.create(user=self.admin_user, group=self.group, role='admin')
        Membership.objects.create(user=self.member_user, group=self.group, role='member')
        self.song = Song.objects.create(
            group=self.group,
            title='Test Song',
            artist='Test Artist',
            key='C'
        )

    def test_detail_member_can_get(self):
        """Member should view song detail (200)."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(f'/api/v1/groups/test-group/songs/{self.song.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Song')

    def test_detail_outsider_cannot_get(self):
        """Outsider should get 403."""
        self.client.force_authenticate(user=self.outsider_user)
        response = self.client.get(f'/api/v1/groups/test-group/songs/{self.song.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_admin_can_update(self):
        """Admin should update song (200)."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'title': 'Updated Song', 'key': 'D'}
        response = self.client.patch(f'/api/v1/groups/test-group/songs/{self.song.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.song.refresh_from_db()
        self.assertEqual(self.song.title, 'Updated Song')

    def test_patch_member_cannot_update(self):
        """Member should get 403."""
        self.client.force_authenticate(user=self.member_user)
        data = {'title': 'Updated Song'}
        response = self.client.patch(f'/api/v1/groups/test-group/songs/{self.song.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_admin_can_delete(self):
        """Admin should delete song (204)."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/v1/groups/test-group/songs/{self.song.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Song.objects.filter(id=self.song.id).exists())

    def test_delete_member_cannot_delete(self):
        """Member should get 403."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(f'/api/v1/groups/test-group/songs/{self.song.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EventSongListViewTests(APITestCase):
    """Test event song (setlist) addition."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )
        self.member_user = CustomUser.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        self.group = Group.objects.create(name='Test Group', slug='test-group')
        Membership.objects.create(user=self.admin_user, group=self.group, role='admin')
        Membership.objects.create(user=self.member_user, group=self.group, role='member')
        self.event = Event.objects.create(
            group=self.group,
            title='Test Event',
            date=datetime.now() + timedelta(days=1),
            created_by=self.admin_user
        )
        self.song = Song.objects.create(
            group=self.group,
            title='Test Song',
            artist='Test Artist'
        )

    def test_list_member_can_list(self):
        """Member should list event songs (200)."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(f'/api/v1/groups/test-group/events/{self.event.id}/songs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_add_song_admin_can_add(self):
        """Admin should add song to event (201)."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'song_id': self.song.id, 'order': 1}
        response = self.client.post(f'/api/v1/groups/test-group/events/{self.event.id}/songs/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            EventSong.objects.filter(event=self.event, song=self.song).exists()
        )
        self.assertEqual(response.data.get('added_by', {}).get('username'), 'admin')
        es = EventSong.objects.get(event=self.event, song=self.song)
        self.assertEqual(es.added_by_id, self.admin_user.id)

    def test_add_song_member_cannot_add(self):
        """Member should get 403."""
        self.client.force_authenticate(user=self.member_user)
        data = {'song_id': self.song.id, 'order': 1}
        response = self.client.post(f'/api/v1/groups/test-group/events/{self.event.id}/songs/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_song_invalid_song_id(self):
        """Invalid song_id should return 400."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'song_id': 99999, 'order': 1}
        response = self.client.post(f'/api/v1/groups/test-group/events/{self.event.id}/songs/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EventSongDetailViewTests(APITestCase):
    """Test event song update and delete."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )
        self.member_user = CustomUser.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        self.group = Group.objects.create(name='Test Group', slug='test-group')
        Membership.objects.create(user=self.admin_user, group=self.group, role='admin')
        Membership.objects.create(user=self.member_user, group=self.group, role='member')
        self.event = Event.objects.create(
            group=self.group,
            title='Test Event',
            date=datetime.now() + timedelta(days=1),
            created_by=self.admin_user
        )
        self.song = Song.objects.create(
            group=self.group,
            title='Test Song',
            artist='Test Artist'
        )
        self.event_song = EventSong.objects.create(
            event=self.event,
            song=self.song,
            order=1
        )

    def test_patch_admin_can_update(self):
        """Admin should update event song order (200)."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'order': 2}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/songs/{self.event_song.id}/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event_song.refresh_from_db()
        self.assertEqual(self.event_song.order, 2)

    def test_patch_member_cannot_update(self):
        """Member should get 403."""
        self.client.force_authenticate(user=self.member_user)
        data = {'order': 2}
        response = self.client.patch(
            f'/api/v1/groups/test-group/events/{self.event.id}/songs/{self.event_song.id}/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_admin_can_delete(self):
        """Admin should delete event song (204)."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(
            f'/api/v1/groups/test-group/events/{self.event.id}/songs/{self.event_song.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EventSong.objects.filter(id=self.event_song.id).exists())

    def test_delete_member_cannot_delete(self):
        """Member should get 403."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(
            f'/api/v1/groups/test-group/events/{self.event.id}/songs/{self.event_song.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SongSuggestionViewTests(APITestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_user(
            username='sadm', email='a@example.com', password='pass123'
        )
        self.member_user = CustomUser.objects.create_user(
            username='smem', email='m@example.com', password='pass123'
        )
        self.outsider_user = CustomUser.objects.create_user(
            username='sout', email='o@example.com', password='pass123'
        )
        self.group = Group.objects.create(name='SG', slug='sg-group')
        Membership.objects.create(user=self.admin_user, group=self.group, role='admin')
        Membership.objects.create(user=self.member_user, group=self.group, role='member')

    def test_member_can_create_suggestion(self):
        self.client.force_authenticate(user=self.member_user)
        r = self.client.post(
            '/api/v1/groups/sg-group/song-suggestions/',
            {'title': 'Nova música', 'artist': 'Artista', 'key': 'C', 'link': 'https://example.com/track'},
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['title'], 'Nova música')
        self.assertEqual(r.data['link'], 'https://example.com/track')
        self.assertEqual(r.data['status'], SongSuggestion.STATUS_PENDING)
        self.assertTrue(SongSuggestion.objects.filter(title='Nova música').exists())

    def test_outsider_cannot_create_suggestion(self):
        self.client.force_authenticate(user=self.outsider_user)
        r = self.client.post(
            '/api/v1/groups/sg-group/song-suggestions/',
            {'title': 'X'},
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_pending_list_admin_sees_suggestion(self):
        SongSuggestion.objects.create(
            group=self.group,
            suggested_by=self.member_user,
            title='Pendente',
            artist='',
        )
        self.client.force_authenticate(user=self.admin_user)
        r = self.client.get('/api/v1/song-suggestions/pending/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]['title'], 'Pendente')

    def test_pending_list_member_empty(self):
        SongSuggestion.objects.create(
            group=self.group,
            suggested_by=self.member_user,
            title='Pendente',
            artist='',
        )
        self.client.force_authenticate(user=self.member_user)
        r = self.client.get('/api/v1/song-suggestions/pending/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 0)

    def test_pending_count(self):
        SongSuggestion.objects.create(
            group=self.group,
            suggested_by=self.member_user,
            title='Pendente',
            artist='',
        )
        self.client.force_authenticate(user=self.admin_user)
        r = self.client.get('/api/v1/song-suggestions/pending-count/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['count'], 1)

    def test_admin_approve_creates_song(self):
        s = SongSuggestion.objects.create(
            group=self.group,
            suggested_by=self.member_user,
            title='Aprovada',
            artist='Art',
            key='D',
            notes='n',
            link='https://ref.example/x',
        )
        self.client.force_authenticate(user=self.admin_user)
        r = self.client.post(f'/api/v1/song-suggestions/{s.id}/approve/', {})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        s.refresh_from_db()
        self.assertEqual(s.status, SongSuggestion.STATUS_APPROVED)
        self.assertIsNotNone(s.created_song_id)
        song = Song.objects.get(pk=s.created_song_id)
        self.assertEqual(song.title, 'Aprovada')
        self.assertEqual(song.link, 'https://ref.example/x')

    def test_admin_reject(self):
        s = SongSuggestion.objects.create(
            group=self.group,
            suggested_by=self.member_user,
            title='Recusada',
            artist='',
        )
        self.client.force_authenticate(user=self.admin_user)
        r = self.client.post(f'/api/v1/song-suggestions/{s.id}/reject/', {})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        s.refresh_from_db()
        self.assertEqual(s.status, SongSuggestion.STATUS_REJECTED)
        self.assertFalse(Song.objects.filter(title='Recusada').exists())

    def test_member_cannot_approve(self):
        s = SongSuggestion.objects.create(
            group=self.group,
            suggested_by=self.member_user,
            title='X',
            artist='',
        )
        self.client.force_authenticate(user=self.member_user)
        r = self.client.post(f'/api/v1/song-suggestions/{s.id}/approve/', {})
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
