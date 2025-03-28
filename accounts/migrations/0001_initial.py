# Generated by Django 5.1.7 on 2025-03-26 19:56

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramBotSettings',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('notification_type', models.CharField(choices=[('SYSTEM', 'System'), ('TRADER', 'Trader'), ('SUPPORT', 'Support')], max_length=50)),
                ('bot_token', models.CharField(max_length=255, verbose_name='Токен телеграм бота')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Сущность токенов телеграм бота',
                'verbose_name_plural': 'Сущность токенов телеграм бота',
            },
        ),
        migrations.CreateModel(
            name='UserAccounts',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('login', models.CharField(max_length=30, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('last_name', models.CharField(blank=True, max_length=255, null=True)),
                ('patronymic_name', models.CharField(blank=True, max_length=255, null=True)),
                ('avatar', models.CharField(blank=True, max_length=255, null=True)),
                ('birthday', models.DateField(blank=True, null=True)),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('MERCHANT', 'Merchant'), ('TRADER', 'Trader'), ('SUPPORT', 'Support')], default='MERCHANT', max_length=10)),
                ('is_active', models.BooleanField(default=True)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('in_consideration', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, related_name='user_accounts_groups', to='auth.group')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='user_accounts_permissions', to='auth.permission')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
