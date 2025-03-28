# Generated by Django 5.1.7 on 2025-03-26 19:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Ожидание'), ('confirmed', 'Подтвержден'), ('canceled', 'Отменен')], default='pending', max_length=20)),
                ('operation', models.CharField(max_length=255)),
                ('declared_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('debit_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('credit_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('details', models.JSONField()),
                ('listing_id', models.IntegerField()),
                ('exchange_rate', models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
