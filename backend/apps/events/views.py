from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models.functions import Coalesce
from django.db.models import F, Value, CharField
from apps.groups.models import Group, Membership
from apps.groups.permissions import IsGroupAdmin, IsGroupMember, user_can_access_event
from .models import Event, EventMember, Song, EventSong, SongSuggestion
from .serializers import (
    EventListSerializer, EventDetailSerializer,
    EventMemberSerializer, SongSerializer, EventSongSerializer,
    SongSuggestionCreateSerializer, SongSuggestionSerializer,
)


class GroupScopedMixin:
    def get_group(self):
        try:
            return Group.objects.get(slug=self.kwargs['slug'])
        except Group.DoesNotExist:
            raise Http404('Grupo não encontrado.')

    def check_group_permission(self, permission_class):
        permission = permission_class()
        if not permission.has_permission(self.request, self):
            raise PermissionDenied()


# --- Events ---

class EventListView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug):
        self.check_group_permission(IsGroupMember)
        group = self.get_group()
        events = Event.objects.filter(group=group).select_related('created_by')

        upcoming = request.query_params.get('upcoming')
        if upcoming in ['true', 'false']:
            from django.utils import timezone
            now = timezone.now()
            if upcoming == 'true':
                events = events.filter(date__gte=now)
            else:
                events = events.filter(date__lt=now)

        date_from = request.query_params.get('date_from')
        if date_from:
            parsed_date_from = parse_datetime(date_from)
            if not parsed_date_from:
                raise ValidationError({'date_from': 'Formato inválido. Use ISO 8601.'})
            events = events.filter(date__gte=parsed_date_from)

        date_to = request.query_params.get('date_to')
        if date_to:
            parsed_date_to = parse_datetime(date_to)
            if not parsed_date_to:
                raise ValidationError({'date_to': 'Formato inválido. Use ISO 8601.'})
            events = events.filter(date__lte=parsed_date_to)

        ordering = request.query_params.get('ordering')
        allowed_ordering = {'date', '-date', 'title', '-title', 'created_at', '-created_at'}
        if ordering:
            if ordering not in allowed_ordering:
                raise ValidationError({'ordering': 'Campo de ordenação inválido.'})
            events = events.order_by(ordering)

        return Response(EventListSerializer(events, many=True).data)

    def post(self, request, slug):
        self.check_group_permission(IsGroupAdmin)
        group = self.get_group()
        serializer = EventListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(group=group, created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventDetailView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return Event.objects.select_related('created_by').prefetch_related(
                'event_members__membership__user',
                'event_members__guest_user',
                'event_songs__song',
                'event_songs__added_by',
            ).get(pk=self.kwargs['pk'], group__slug=self.kwargs['slug'])
        except Event.DoesNotExist:
            raise Http404('Evento não encontrado.')

    def get(self, request, slug, pk):
        event = self.get_object()
        if not user_can_access_event(request.user, slug, event.pk):
            raise PermissionDenied()
        return Response(EventDetailSerializer(event, context={'request': request}).data)

    def patch(self, request, slug, pk):
        self.check_group_permission(IsGroupAdmin)
        event = self.get_object()
        serializer = EventDetailSerializer(event, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, slug, pk):
        self.check_group_permission(IsGroupAdmin)
        event = self.get_object()
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Event Members ---

class EventMemberListView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug, pk):
        group = self.get_group()
        try:
            Event.objects.get(pk=pk, group__slug=slug)
        except Event.DoesNotExist:
            raise Http404('Evento não encontrado.')
        if not user_can_access_event(request.user, slug, int(pk)):
            raise PermissionDenied()

        members = (
            EventMember.objects.filter(event__pk=pk, event__group__slug=slug)
            .select_related('membership__user', 'guest_user')
            .annotate(
                sort_name=Coalesce(
                    F('guest_user__username'),
                    F('membership__user__username'),
                    Value(''),
                    output_field=CharField(),
                )
            )
            .order_by('sort_name')
        )
        return Response(
            EventMemberSerializer(
                members, many=True, context={'group': group, 'request': request}
            ).data
        )

    def post(self, request, slug, pk):
        self.check_group_permission(IsGroupAdmin)
        group = self.get_group()
        try:
            event = Event.objects.get(pk=pk, group__slug=slug)
        except Event.DoesNotExist:
            raise Http404('Evento não encontrado.')

        serializer = EventMemberSerializer(
            data=request.data, context={'group': group, 'event': event, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(event=event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventMemberDetailView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return EventMember.objects.get(
                pk=self.kwargs['member_pk'],
                event__pk=self.kwargs['pk'],
                event__group__slug=self.kwargs['slug']
            )
        except EventMember.DoesNotExist:
            raise Http404('Membro do evento não encontrado.')

    def patch(self, request, slug, pk, member_pk):
        self.check_group_permission(IsGroupAdmin)
        group = self.get_group()
        member = self.get_object()
        serializer = EventMemberSerializer(
            member,
            data=request.data,
            partial=True,
            context={'group': group, 'event': member.event, 'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, slug, pk, member_pk):
        self.check_group_permission(IsGroupAdmin)
        member = self.get_object()
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ParticipationView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, slug, pk, member_pk):
        group = self.get_group()

        try:
            event_member = EventMember.objects.get(
                pk=member_pk,
                event__pk=pk,
                event__group__slug=slug,
            )
        except EventMember.DoesNotExist:
            raise Http404('Participação não encontrada.')
        if not user_can_access_event(request.user, slug, int(pk)):
            raise PermissionDenied()

        user = request.user
        if event_member.membership_id:
            if event_member.membership.user_id != user.id:
                raise Http404('Participação não encontrada.')
        elif event_member.guest_user_id:
            if event_member.guest_user_id != user.id:
                raise Http404('Participação não encontrada.')
        else:
            raise Http404('Participação não encontrada.')

        participation = request.data.get('participation')
        if participation not in ['confirmed', 'declined', 'pending']:
            raise ValidationError({'participation': 'Valor inválido.'})

        event_member.participation = participation
        event_member.save()
        return Response(
            EventMemberSerializer(event_member, context={'group': group, 'request': request}).data
        )


# --- Songs (library) ---

class SongListView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug):
        self.check_group_permission(IsGroupMember)
        group = self.get_group()
        songs = Song.objects.filter(group=group).order_by('title')
        return Response(SongSerializer(songs, many=True).data)

    def post(self, request, slug):
        self.check_group_permission(IsGroupAdmin)
        group = self.get_group()
        serializer = SongSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(group=group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SongDetailView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return Song.objects.get(pk=self.kwargs['song_pk'], group__slug=self.kwargs['slug'])
        except Song.DoesNotExist:
            raise Http404('Música não encontrada.')

    def get(self, request, slug, song_pk):
        self.check_group_permission(IsGroupMember)
        song = self.get_object()
        return Response(SongSerializer(song).data)

    def patch(self, request, slug, song_pk):
        self.check_group_permission(IsGroupAdmin)
        song = self.get_object()
        serializer = SongSerializer(song, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, slug, song_pk):
        self.check_group_permission(IsGroupAdmin)
        song = self.get_object()
        song.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Event Songs (setlist) ---

class EventSongListView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug, pk):
        group = self.get_group()
        try:
            Event.objects.get(pk=pk, group__slug=slug)
        except Event.DoesNotExist:
            raise Http404('Evento não encontrado.')
        if not user_can_access_event(request.user, slug, int(pk)):
            raise PermissionDenied()

        songs = EventSong.objects.filter(
            event__pk=pk,
            event__group__slug=slug
        ).select_related('song', 'added_by').order_by('order')
        return Response(
            EventSongSerializer(songs, many=True, context={'group': group, 'request': request}).data
        )

    def post(self, request, slug, pk):
        self.check_group_permission(IsGroupAdmin)
        group = self.get_group()
        try:
            event = Event.objects.get(pk=pk, group__slug=slug)
        except Event.DoesNotExist:
            raise Http404('Evento não encontrado.')

        serializer = EventSongSerializer(
            data=request.data, context={'group': group, 'event': event, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(event=event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventSongDetailView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return EventSong.objects.get(
                pk=self.kwargs['esong_pk'],
                event__pk=self.kwargs['pk'],
                event__group__slug=self.kwargs['slug']
            )
        except EventSong.DoesNotExist:
            raise Http404('Música do evento não encontrada.')

    def patch(self, request, slug, pk, esong_pk):
        self.check_group_permission(IsGroupAdmin)
        group = self.get_group()
        event_song = self.get_object()
        serializer = EventSongSerializer(
            event_song, data=request.data, partial=True, context={'group': group, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, slug, pk, esong_pk):
        self.check_group_permission(IsGroupAdmin)
        event_song = self.get_object()
        event_song.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Song suggestions ---


class SongSuggestionCreateView(GroupScopedMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        self.check_group_permission(IsGroupMember)
        group = self.get_group()
        ser = SongSuggestionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        suggestion = SongSuggestion.objects.create(
            group=group,
            suggested_by=request.user,
            **ser.validated_data,
        )
        return Response(
            SongSuggestionSerializer(suggestion, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class SongSuggestionPendingListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        admin_group_ids = Membership.objects.filter(
            user=request.user, role='admin'
        ).values_list('group_id', flat=True)
        qs = (
            SongSuggestion.objects.filter(status=SongSuggestion.STATUS_PENDING, group_id__in=admin_group_ids)
            .select_related('group', 'suggested_by', 'reviewed_by')
            .order_by('-created_at')
        )
        return Response(SongSuggestionSerializer(qs, many=True, context={'request': request}).data)


class SongSuggestionPendingCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        admin_group_ids = Membership.objects.filter(
            user=request.user, role='admin'
        ).values_list('group_id', flat=True)
        n = SongSuggestion.objects.filter(
            status=SongSuggestion.STATUS_PENDING, group_id__in=admin_group_ids
        ).count()
        return Response({'count': n})


class SongSuggestionApproveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        with transaction.atomic():
            try:
                suggestion = SongSuggestion.objects.select_for_update().get(pk=pk)
            except SongSuggestion.DoesNotExist:
                raise Http404('Sugestão não encontrada.')
            if not Membership.objects.filter(
                user=request.user, group=suggestion.group, role='admin'
            ).exists():
                raise PermissionDenied()
            if suggestion.status != SongSuggestion.STATUS_PENDING:
                raise ValidationError({'detail': 'Esta sugestão já foi respondida.'})
            song = Song.objects.create(
                group=suggestion.group,
                title=suggestion.title,
                artist=suggestion.artist,
                key=suggestion.key,
                notes=suggestion.notes,
                link=suggestion.link,
            )
            suggestion.status = SongSuggestion.STATUS_APPROVED
            suggestion.reviewed_by = request.user
            suggestion.reviewed_at = timezone.now()
            suggestion.created_song = song
            suggestion.save(
                update_fields=['status', 'reviewed_by', 'reviewed_at', 'created_song_id']
            )
        return Response(SongSuggestionSerializer(suggestion, context={'request': request}).data)


class SongSuggestionRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        with transaction.atomic():
            try:
                suggestion = SongSuggestion.objects.select_for_update().get(pk=pk)
            except SongSuggestion.DoesNotExist:
                raise Http404('Sugestão não encontrada.')
            if not Membership.objects.filter(
                user=request.user, group=suggestion.group, role='admin'
            ).exists():
                raise PermissionDenied()
            if suggestion.status != SongSuggestion.STATUS_PENDING:
                raise ValidationError({'detail': 'Esta sugestão já foi respondida.'})
            suggestion.status = SongSuggestion.STATUS_REJECTED
            suggestion.reviewed_by = request.user
            suggestion.reviewed_at = timezone.now()
            suggestion.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        return Response(SongSuggestionSerializer(suggestion, context={'request': request}).data)
