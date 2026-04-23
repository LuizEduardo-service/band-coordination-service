from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUser(AbstractUser):
    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='usuário',
    )
    phone = models.CharField(max_length=30, blank=True, verbose_name='telefone')
    bio = models.TextField(blank=True, verbose_name='sobre mim')
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name='foto')
    instruments = models.JSONField(default=list, blank=True, verbose_name='instrumentos')

    class Meta:
        verbose_name = 'perfil'
        verbose_name_plural = 'perfis'

    def __str__(self) -> str:
        return f'Perfil de {self.user.username}'


@receiver(post_save, sender=CustomUser)
def ensure_user_profile(sender, instance, created, **kwargs):
    if kwargs.get('raw'):
        return
    UserProfile.objects.get_or_create(user=instance)
