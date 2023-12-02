# Generated by Django 4.2.7 on 2023-12-02 17:58

import django.db.models.deletion
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='profile', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('avatar', models.ImageField(null=True, upload_to='avatars')),
            ],
        ),
    ]
