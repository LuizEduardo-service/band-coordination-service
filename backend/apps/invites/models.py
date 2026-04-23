from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import CustomUser
from apps.events.models import Event
from apps.groups.models import Group


class Invite(models.Model):
    KIND_GROUP = 'group'
    KIND_EVENT = 'event'
    KIND_CHOICES = [(KIND_GROUP, 'Grupo'), (KIND_EVENT, 'Evento')]

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_ACCEPTED, 'Aceito'),
        (STATUS_DECLINED, 'Recusado'),
    ]

    inviter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='invites_sent',
        verbose_name='quem convida',
    )
    invitee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='invites_received',
        verbose_name='convidado',
    )
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invites',
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invites',
    )
    role = models.CharField(
        max_length=20,
        default='member',
        help_text='Papel no grupo ao aceitar (admin ou member).',
    )
    role_in_event = models.CharField(max_length=50, blank=True, verbose_name='papel no evento')
    instruments = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'convite'
        verbose_name_plural = 'convites'
        constraints = [
            models.UniqueConstraint(
                fields=['invitee', 'group'],
                condition=models.Q(kind='group', status='pending'),
                name='invite_unique_pending_group',
            ),
            models.UniqueConstraint(
                fields=['invitee', 'event'],
                condition=models.Q(kind='event', status='pending'),
                name='invite_unique_pending_event',
            ),
        ]

    def clean(self):
        super().clean()
        if self.kind == self.KIND_GROUP:
            if not self.group_id:
                raise ValidationError({'group': 'Grupo obrigatório para convite de grupo.'})
            if self.event_id:
                raise ValidationError({'event': 'Convite de grupo não deve referenciar evento.'})
        elif self.kind == self.KIND_EVENT:
            if not self.event_id:
                raise ValidationError({'event': 'Evento obrigatório para convite de evento.'})
            if self.group_id and self.event and self.group_id != self.event.group_id:
                raise ValidationError({'group': 'Grupo inconsistente com o evento.'})
        if self.inviter_id and self.invitee_id and self.inviter_id == self.invitee_id:
            raise ValidationError('Não é possível convidar a si mesmo.')

    def __str__(self):
        return f'{self.get_kind_display()} → {self.invitee} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if self.kind == self.KIND_EVENT and self.event_id and not self.group_id:
            self.group_id = Event.objects.filter(pk=self.event_id).values_list('group_id', flat=True).first()
        super().save(*args, **kwargs)

    def mark_responded(self, new_status: str) -> None:
        self.status = new_status
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
