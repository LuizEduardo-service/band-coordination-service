from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from .models import Group, Membership


class GroupSerializer(serializers.ModelSerializer):
    my_role = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'is_active', 'avatar', 'avatar_url', 'my_role']
        read_only_fields = ['id', 'slug', 'created_at', 'is_active', 'avatar_url', 'my_role']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_my_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        role = (
            Membership.objects.filter(user=request.user, group=obj)
            .values_list('role', flat=True)
            .first()
        )
        return role


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'user', 'user_id', 'role', 'is_vocalist', 'joined_at']
        read_only_fields = ['id', 'joined_at']
