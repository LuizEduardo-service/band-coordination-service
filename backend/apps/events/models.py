from django.core.exceptions import ValidationError
from django.db import models
from apps.accounts.models import CustomUser
from apps.groups.models import Group, Membership


class Event(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200, verbose_name='título')
    date = models.DateTimeField(verbose_name='data')
    description = models.TextField(blank=True, verbose_name='descrição')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'
        ordering = ['-date']

    def __str__(self):
        return f'{self.title} — {self.date.strftime("%d/%m/%Y")}'


class EventMember(models.Model):
    PARTICIPATION_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('declined', 'Recusado'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_members')
    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='event_assignments',
    )
    guest_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='event_guest_assignments',
        verbose_name='usuário convidado (sem membership no grupo)',
    )
    participation = models.CharField(max_length=20, choices=PARTICIPATION_CHOICES, default='pending')
    role_in_event = models.CharField(max_length=50, blank=True, verbose_name='papel no evento')
    instruments = models.JSONField(default=list, verbose_name='instrumentos neste evento')

    class Meta:
        verbose_name = 'membro do evento'
        verbose_name_plural = 'membros do evento'
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'membership'],
                condition=models.Q(membership__isnull=False),
                name='eventmember_unique_event_membership',
            ),
            models.UniqueConstraint(
                fields=['event', 'guest_user'],
                condition=models.Q(guest_user__isnull=False),
                name='eventmember_unique_event_guest_user',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(membership__isnull=False, guest_user__isnull=True)
                    | models.Q(membership__isnull=True, guest_user__isnull=False)
                ),
                name='eventmember_membership_xor_guest',
            ),
        ]

    def clean(self):
        super().clean()
        has_m = self.membership_id is not None
        has_g = self.guest_user_id is not None
        if has_m and has_g:
            raise ValidationError('Use apenas membership (membro do grupo) ou guest_user (só evento).')
        if not has_m and not has_g:
            raise ValidationError('Informe membership ou guest_user.')

    def __str__(self):
        if self.membership_id:
            return f'{self.membership} — {self.event.title} ({self.get_participation_display()})'
        return f'{self.guest_user} (convidado) — {self.event.title} ({self.get_participation_display()})'


class Song(models.Model):
    KEY_CHOICES = [
        ('C', 'Dó Maior'),    ('Cm', 'Dó Menor'),
        ('C#', 'Dó# Maior'),  ('C#m', 'Dó# Menor'),
        ('Db', 'Réb Maior'),
        ('D', 'Ré Maior'),    ('Dm', 'Ré Menor'),
        ('D#m', 'Ré# Menor'),
        ('Eb', 'Mib Maior'),
        ('E', 'Mi Maior'),    ('Em', 'Mi Menor'),
        ('F', 'Fá Maior'),    ('Fm', 'Fá Menor'),
        ('F#', 'Fá# Maior'),  ('F#m', 'Fá# Menor'),
        ('G', 'Sol Maior'),   ('Gm', 'Sol Menor'),
        ('G#m', 'Sol# Menor'),
        ('Ab', 'Láb Maior'),
        ('A', 'Lá Maior'),    ('Am', 'Lá Menor'),
        ('A#m', 'Lá# Menor'),
        ('Bb', 'Sib Maior'),
        ('B', 'Si Maior'),    ('Bm', 'Si Menor'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='songs')
    title = models.CharField(max_length=200, verbose_name='título')
    artist = models.CharField(max_length=200, blank=True, verbose_name='artista')
    key = models.CharField(max_length=5, choices=KEY_CHOICES, blank=True, verbose_name='tonalidade')
    notes = models.TextField(blank=True, verbose_name='observações')
    link = models.URLField(
        blank=True,
        verbose_name='link de referência',
        help_text='URL opcional (streaming, vídeo, partitura, etc.).',
    )

    class Meta:
        verbose_name = 'música'
        verbose_name_plural = 'músicas'
        ordering = ['title']

    def __str__(self):
        return f'{self.title} ({self.artist})' if self.artist else self.title


class SongSuggestion(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_APPROVED, 'Aprovada'),
        (STATUS_REJECTED, 'Recusada'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='song_suggestions')
    suggested_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='song_suggestions',
        verbose_name='sugerido por',
    )
    title = models.CharField(max_length=200, verbose_name='título')
    artist = models.CharField(max_length=200, blank=True, verbose_name='artista')
    key = models.CharField(max_length=5, choices=Song.KEY_CHOICES, blank=True, verbose_name='tonalidade')
    notes = models.TextField(blank=True, verbose_name='observações')
    link = models.URLField(
        blank=True,
        verbose_name='link de referência',
        help_text='URL opcional (streaming, vídeo, partitura, etc.).',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='song_suggestions_reviewed',
        verbose_name='revisado por',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_song = models.ForeignKey(
        Song,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_suggestion',
        verbose_name='música criada',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'sugestão de música'
        verbose_name_plural = 'sugestões de música'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'group']),
        ]

    def __str__(self):
        return f'{self.title} — {self.group} ({self.get_status_display()})'


class EventSong(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='event_songs')
    order = models.PositiveIntegerField(default=0, verbose_name='ordem')
    added_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='event_songs_added',
        verbose_name='incluída por',
    )

    class Meta:
        unique_together = ('event', 'song')
        ordering = ['order']
        verbose_name = 'música do evento'
        verbose_name_plural = 'músicas do evento'

    def __str__(self):
        return f'{self.order}. {self.song.title} — {self.event.title}'
