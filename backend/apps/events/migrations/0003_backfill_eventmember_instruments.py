from django.db import migrations


def backfill_eventmember_instruments(apps, schema_editor):
    EventMember = apps.get_model('events', 'EventMember')
    for em in EventMember.objects.all().select_related('membership__user'):
        if em.instruments:
            continue
        user = em.membership.user
        inst = list(user.instruments or [])
        em.instruments = inst[:1] if inst else ['other']
        em.save(update_fields=['instruments'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_profile_and_instruments'),
        ('groups', '0002_profile_and_instruments'),
    ]

    operations = [
        migrations.RunPython(backfill_eventmember_instruments, noop_reverse),
    ]
