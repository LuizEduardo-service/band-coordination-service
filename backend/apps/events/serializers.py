from rest_framework import serializers
from django.utils import timezone
from apps.accounts.models import UserProfile
from apps.accounts.serializers import UserSerializer
from apps.groups.serializers import MembershipSerializer
from apps.groups.models import Membership
from apps.common.instruments import validate_instruments_list
from .models import Event, EventMember, Song, EventSong, SongSuggestion


def _user_instruments_list(user):
    try:
        return list(user.profile.instruments or [])
    except UserProfile.DoesNotExist:
        return []


class SongSerializer(serializers.ModelSerializer):
    key_display = serializers.CharField(source='get_key_display', read_only=True)

    class Meta:
        model = Song
        fields = ['id', 'title', 'artist', 'key', 'key_display', 'notes', 'link']
        read_only_fields = ['id']


class SongSuggestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SongSuggestion
        fields = ['title', 'artist', 'key', 'notes', 'link']

    def validate_title(self, value):
        if not (value or '').strip():
            raise serializers.ValidationError('Título é obrigatório.')
        return value.strip()


class SongSuggestionSerializer(serializers.ModelSerializer):
    suggested_by = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    group_slug = serializers.CharField(source='group.slug', read_only=True)
    key_display = serializers.CharField(source='get_key_display', read_only=True)
    created_song_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = SongSuggestion
        fields = [
            'id',
            'group_name',
            'group_slug',
            'suggested_by',
            'title',
            'artist',
            'key',
            'key_display',
            'notes',
            'link',
            'status',
            'reviewed_by',
            'reviewed_at',
            'created_song_id',
            'created_at',
        ]
        read_only_fields = fields


class EventSongSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    song_id = serializers.IntegerField(write_only=True)
    added_by = UserSerializer(read_only=True)

    class Meta:
        model = EventSong
        fields = ['id', 'song', 'song_id', 'order', 'added_by']
        read_only_fields = ['id', 'added_by']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            validated_data['added_by'] = request.user
        return super().create(validated_data)

    def validate_song_id(self, value):
        group = self.context.get('group')
        if not group:
            raise serializers.ValidationError('Grupo não fornecido no contexto.')
        try:
            song = Song.objects.get(pk=value, group=group)
        except Song.DoesNotExist:
            raise serializers.ValidationError('Música não pertence a este grupo.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        event = self.instance.event if self.instance else self.context.get('event')
        song_id = attrs.get('song_id')
        if event and song_id:
            already_exists = EventSong.objects.filter(event=event, song_id=song_id)
            if self.instance:
                already_exists = already_exists.exclude(pk=self.instance.pk)
            if already_exists.exists():
                raise serializers.ValidationError({'song_id': 'Música já adicionada ao evento.'})
        return attrs


class EventMemberSerializer(serializers.ModelSerializer):
    membership = MembershipSerializer(read_only=True, allow_null=True)
    membership_id = serializers.IntegerField(write_only=True, required=False)
    user = serializers.SerializerMethodField()

    class Meta:
        model = EventMember
        fields = [
            'id',
            'user',
            'membership',
            'membership_id',
            'participation',
            'role_in_event',
            'instruments',
        ]
        read_only_fields = ['id', 'user']

    def get_user(self, obj):
        u = obj.membership.user if obj.membership_id else obj.guest_user
        if not u:
            return None
        return UserSerializer(u, context=self.context).data

    def validate_instruments(self, value):
        validate_instruments_list(value)
        if len(value) < 1:
            raise serializers.ValidationError('Informe ao menos um instrumento.')
        return value

    def validate_membership_id(self, value):
        group = self.context.get('group')
        if not group:
            raise serializers.ValidationError('Grupo não fornecido no contexto.')
        try:
            Membership.objects.get(pk=value, group=group)
        except Membership.DoesNotExist:
            raise serializers.ValidationError('Membro não pertence a este grupo.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        group = self.context.get('group')
        event = self.instance.event if self.instance else self.context.get('event')
        membership_id = attrs.get('membership_id')

        if event and membership_id is not None:
            already_exists = EventMember.objects.filter(event=event, membership_id=membership_id)
            if self.instance:
                already_exists = already_exists.exclude(pk=self.instance.pk)
            if already_exists.exists():
                raise serializers.ValidationError({'membership_id': 'Membro já associado ao evento.'})

        if not group:
            return attrs

        instruments = attrs.get('instruments')
        if instruments is None:
            return attrs

        membership = None
        guest_user = None
        if self.instance:
            membership = self.instance.membership
            guest_user = self.instance.guest_user
        elif membership_id is not None:
            membership = Membership.objects.get(pk=membership_id, group=group)

        subject_user = membership.user if membership else guest_user
        if subject_user and instruments is not None:
            allowed = set(_user_instruments_list(subject_user))
            if not allowed:
                raise serializers.ValidationError(
                    {'instruments': 'O usuário precisa ter instrumentos cadastrados no perfil.'}
                )
            for i in instruments:
                if i not in allowed:
                    raise serializers.ValidationError(
                        {'instruments': f'Instrumento "{i}" não está no perfil do usuário.'}
                    )
        return attrs

    def create(self, validated_data):
        membership_id = validated_data.pop('membership_id', None)
        if membership_id is None:
            raise serializers.ValidationError({'membership_id': 'Obrigatório para adicionar membro do grupo ao evento.'})
        event = self.context['event']
        membership = Membership.objects.get(pk=membership_id, group=event.group)
        return EventMember.objects.create(
            event=event,
            membership=membership,
            guest_user=None,
            participation=validated_data.get('participation', 'pending'),
            role_in_event=validated_data.get('role_in_event', ''),
            instruments=validated_data['instruments'],
        )


class EventListSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source='event_members.count', read_only=True)
    song_count = serializers.IntegerField(source='event_songs.count', read_only=True)
    is_past = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'date',
            'description',
            'member_count',
            'song_count',
            'is_past',
            'is_upcoming',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_is_past(self, obj):
        return obj.date < timezone.now()

    def get_is_upcoming(self, obj):
        return obj.date >= timezone.now()


class EventDetailSerializer(serializers.ModelSerializer):
    event_members = EventMemberSerializer(many=True, read_only=True)
    event_songs = EventSongSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'title', 'date', 'description', 'created_by', 'created_at', 'event_members', 'event_songs']
        read_only_fields = ['id', 'created_by', 'created_at']
