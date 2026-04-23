from django.db import migrations, models
import django.db.models.deletion


def copy_user_profile_fields(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    for u in CustomUser.objects.all():
        UserProfile.objects.update_or_create(
            user=u,
            defaults={
                'phone': u.phone,
                'bio': u.bio,
                'photo': u.photo,
                'instruments': list(u.instruments or []),
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_and_instruments'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=30, verbose_name='telefone')),
                ('bio', models.TextField(blank=True, verbose_name='sobre mim')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='profiles/', verbose_name='foto')),
                ('instruments', models.JSONField(blank=True, default=list, verbose_name='instrumentos')),
                (
                    'user',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='profile',
                        to='accounts.customuser',
                        verbose_name='usuário',
                    ),
                ),
            ],
            options={
                'verbose_name': 'perfil',
                'verbose_name_plural': 'perfis',
            },
        ),
        migrations.RunPython(copy_user_profile_fields, migrations.RunPython.noop),
        migrations.RemoveField(model_name='customuser', name='bio'),
        migrations.RemoveField(model_name='customuser', name='instruments'),
        migrations.RemoveField(model_name='customuser', name='phone'),
        migrations.RemoveField(model_name='customuser', name='photo'),
    ]
