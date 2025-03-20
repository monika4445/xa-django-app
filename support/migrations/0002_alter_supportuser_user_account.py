# Generated by Django 5.1.7 on 2025-03-20 06:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_useraccounts_groups_and_more'),
        ('support', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supportuser',
            name='user_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support_user', to='accounts.useraccounts', verbose_name='Аккаунт пользователя'),
        ),
    ]
