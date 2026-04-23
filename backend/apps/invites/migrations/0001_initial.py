import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events', '0005_eventmember_guest_user'),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('group', 'Grupo'), ('event', 'Evento')], max_length=10)),
                (
                    'role',
                    models.CharField(
                        default='member',
                        help_text='Papel no grupo ao aceitar (admin ou member).',
                        max_length=20,
                    ),
                ),
                ('role_in_event', models.CharField(blank=True, max_length=50, verbose_name='papel no evento')),
                ('instruments', models.JSONField(blank=True, default=list)),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('pending', 'Pendente'),
                            ('accepted', 'Aceito'),
                            ('declined', 'Recusado'),
                        ],
                        default='pending',
                        max_length=20,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                (
                    'event',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='invites',
                        to='events.event',
                    ),
                ),
                (
                    'group',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='invites',
                        to='groups.group',
                    ),
                ),
                (
                    'invitee',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='invites_received',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='convidado',
                    ),
                ),
                (
                    'inviter',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='invites_sent',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='quem convida',
                    ),
                ),
            ],
            options={
                'verbose_name': 'convite',
                'verbose_name_plural': 'convites',
            },
        ),
        migrations.AddConstraint(
            model_name='invite',
            constraint=models.UniqueConstraint(
                condition=models.Q(kind='group', status='pending'),
                fields=('invitee', 'group'),
                name='invite_unique_pending_group',
            ),
        ),
        migrations.AddConstraint(
            model_name='invite',
            constraint=models.UniqueConstraint(
                condition=models.Q(kind='event', status='pending'),
                fields=('invitee', 'event'),
                name='invite_unique_pending_event',
            ),
        ),
    ]
