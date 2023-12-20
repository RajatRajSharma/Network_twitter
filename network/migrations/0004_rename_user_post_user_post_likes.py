# Generated by Django 4.2.7 on 2023-12-18 09:29

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0003_like'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='User',
            new_name='user',
        ),
        migrations.AddField(
            model_name='post',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_posts', to=settings.AUTH_USER_MODEL),
        ),
    ]