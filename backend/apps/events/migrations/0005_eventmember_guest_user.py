import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events', '0004_eventsong_added_by'),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='eventmember',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='eventmember',
            name='guest_user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='event_guest_assignments',
                to=settings.AUTH_USER_MODEL,
                verbose_name='usuário convidado (sem membership no grupo)',
            ),
        ),
        migrations.AlterField(
            model_name='eventmember',
            name='membership',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='event_assignments',
                to='groups.membership',
            ),
        ),
        migrations.AddConstraint(
            model_name='eventmember',
            constraint=models.UniqueConstraint(
                condition=models.Q(membership__isnull=False),
                fields=('event', 'membership'),
                name='eventmember_unique_event_membership',
            ),
        ),
        migrations.AddConstraint(
            model_name='eventmember',
            constraint=models.UniqueConstraint(
                condition=models.Q(guest_user__isnull=False),
                fields=('event', 'guest_user'),
                name='eventmember_unique_event_guest_user',
            ),
        ),
        migrations.AddConstraint(
            model_name='eventmember',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(membership__isnull=False, guest_user__isnull=True)
                    | models.Q(membership__isnull=True, guest_user__isnull=False)
                ),
                name='eventmember_membership_xor_guest',
            ),
        ),
    ]
