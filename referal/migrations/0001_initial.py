# Generated by Django 5.1.7 on 2025-03-26 19:56

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReferalUser',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('user_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referal_user', to=settings.AUTH_USER_MODEL, verbose_name='Аккаунт пользователя')),
            ],
        ),
    ]
