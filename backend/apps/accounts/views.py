from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CustomUser, UserProfile
from .serializers import UserSerializer, RegisterSerializer, ChangePasswordSerializer


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)

    def patch(self, request):
        serializer = UserSerializer(
            request.user, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MePhotoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        photo = request.FILES.get('photo')
        if not photo:
            raise ValidationError({'photo': 'Envie o arquivo no campo "photo".'})
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.photo = photo
        profile.save(update_fields=['photo'])
        return Response(UserSerializer(request.user, context={'request': request}).data)


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Senha alterada com sucesso.'})


class UserSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('search', '').strip()
        if len(q) < 2:
            return Response([])
        # TODO: Add rate limiting (e.g., via django-ratelimit or throttling)
        users = CustomUser.objects.filter(username__icontains=q).select_related('profile')[:10]
        return Response(UserSerializer(users, many=True, context={'request': request}).data)
