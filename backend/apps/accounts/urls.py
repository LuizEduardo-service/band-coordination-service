from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, MeView, MePhotoView, ChangePasswordView, UserSearchView

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/me/photo/', MePhotoView.as_view(), name='me_photo'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('users/', UserSearchView.as_view(), name='user_search'),
]
