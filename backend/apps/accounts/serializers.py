from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from apps.common.instruments import validate_instruments_list
from .models import CustomUser, UserProfile


def _profile_for(user):
    """Lê o perfil pelo banco para evitar cache stale do OneToOne reverso após save()."""
    if not getattr(user, 'pk', None):
        return None
    return UserProfile.objects.filter(user_id=user.pk).first()


class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    bio = serializers.CharField(write_only=True, required=False, allow_blank=True)
    instruments = serializers.JSONField(write_only=True, required=False)
    photo = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'bio',
            'instruments',
            'photo',
        ]
        read_only_fields = ['id', 'username', 'photo']

    def get_photo(self, obj):
        prof = _profile_for(obj)
        if not prof or not prof.photo:
            return None
        request = self.context.get('request')
        url = prof.photo.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def validate_instruments(self, value):
        if value is None:
            return value
        validate_instruments_list(value)
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        prof = _profile_for(instance)
        data['phone'] = prof.phone if prof else ''
        data['bio'] = prof.bio if prof else ''
        data['instruments'] = list(prof.instruments or []) if prof else []
        data['photo'] = self.get_photo(instance)
        return data

    def update(self, instance, validated_data):
        profile_patch = {}
        for key in ('phone', 'bio', 'instruments'):
            if key in validated_data:
                profile_patch[key] = validated_data.pop(key)
        user = super().update(instance, validated_data)
        if profile_patch:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            for k, v in profile_patch.items():
                setattr(profile, k, v)
            profile.save()
            # Evita que user.profile (cache do descriptor) fique com instância antiga.
            user.__dict__.pop('profile', None)
        return user


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']

    def validate_email(self, value):
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Este e-mail já está em uso.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Senhas não conferem.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return CustomUser.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta.')
        return value
