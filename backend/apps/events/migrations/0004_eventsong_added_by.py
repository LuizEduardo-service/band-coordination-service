import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events', '0003_backfill_eventmember_instruments'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventsong',
            name='added_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='event_songs_added',
                to=settings.AUTH_USER_MODEL,
                verbose_name='incluída por',
            ),
        ),
    ]
