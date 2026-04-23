from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.common.instruments import validate_instruments_list
from .models import Invite


class InviteSerializer(serializers.ModelSerializer):
    inviter = UserSerializer(read_only=True)
    group_slug = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    event_id = serializers.IntegerField(read_only=True)
    event_title = serializers.SerializerMethodField()

    class Meta:
        model = Invite
        fields = [
            'id',
            'kind',
            'status',
            'inviter',
            'group_slug',
            'group_name',
            'event_id',
            'event_title',
            'role',
            'role_in_event',
            'instruments',
            'created_at',
            'responded_at',
        ]
        read_only_fields = [
            'id',
            'kind',
            'status',
            'inviter',
            'group_slug',
            'group_name',
            'event_id',
            'event_title',
            'role',
            'role_in_event',
            'instruments',
            'created_at',
            'responded_at',
        ]

    def get_group_slug(self, obj):
        if obj.group_id:
            return obj.group.slug
        if obj.event_id:
            return obj.event.group.slug
        return None

    def get_group_name(self, obj):
        if obj.group_id:
            return obj.group.name
        if obj.event_id:
            return obj.event.group.name
        return None

    def get_event_title(self, obj):
        if obj.event_id:
            return obj.event.title
        return None


class GroupInviteCreateSerializer(serializers.Serializer):
    invitee_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=['admin', 'member'], default='member')


class EventInviteCreateSerializer(serializers.Serializer):
    invitee_id = serializers.IntegerField()
    instruments = serializers.ListField(child=serializers.CharField(), min_length=1)
    role_in_event = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_instruments(self, value):
        validate_instruments_list(value)
        return value
