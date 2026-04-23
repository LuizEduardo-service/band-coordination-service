from django.db import models
from django.utils.text import slugify
from apps.accounts.models import CustomUser


class Group(models.Model):
    name = models.CharField(max_length=200, verbose_name='nome')
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name='descrição')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name='ativo')
    avatar = models.ImageField(upload_to='group_avatars/', null=True, blank=True, verbose_name='avatar')

    class Meta:
        verbose_name = 'grupo'
        verbose_name_plural = 'grupos'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Membership(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('member', 'Membro')]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    is_vocalist = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'group')
        verbose_name = 'membro'
        verbose_name_plural = 'membros'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} — {self.group.name}'
