from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Perfil'
    verbose_name_plural = 'Dados de perfil'
    fields = ('phone', 'bio', 'instruments', 'photo')
    extra = 0


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    inlines = (UserProfileInline,)
