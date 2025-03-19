import uuid

from django.db import models
from django.contrib.postgres.fields import ArrayField


class Appeal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order_id = models.CharField(max_length=255, unique=True)
    invoice_id = models.CharField(max_length=255, unique=True)

    amount = models.FloatField(default=.00, verbose_name='Стоимость')

    sup_id = models.ForeignKey("SupportUser", on_delete=models.CASCADE, verbose_name='Пользователь поддержки')

    provider_id = models.ForeignKey("trader.Provider", blank=True, null=True, on_delete=models.CASCADE, verbose_name='Провайдер')
    responsible_id = models.ForeignKey("trader.Trader", blank=True, null=True, on_delete=models.CASCADE, verbose_name='Трейдер')

    class AppealStatus(models.TextChoices):
        PENDING = 'pending'
        COMPLETED = 'confirmed'
        EXPIRED = 'expired'
        DISPUTE = 'dispute'
        CANCELED = 'canceled'
    status = models.CharField(max_length=50, choices=AppealStatus.choices, default=AppealStatus.PENDING)

    expiration_at = models.DateTimeField(blank=True, null=True)
    source_id = models.ForeignKey("merchant.Merchant", on_delete=models.CASCADE, verbose_name='Мерчант')

    documents = ArrayField(models.CharField(max_length=100), default=list)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность запроса в службу поддержки"
        verbose_name_plural = "Сущность запроса в службу поддержки"


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='reports/', verbose_name='Документ')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность документов"
        verbose_name_plural = "Сущность документов"


class SupportUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_account = models.ForeignKey(
        "accounts.UserAccounts",
        on_delete=models.CASCADE,
        related_name="support_user",
        verbose_name="Аккаунт пользователя"
    )

    email = models.CharField(max_length=255, verbose_name="Почта")
    hash_password = models.CharField(max_length=255, verbose_name='Хешированный пароль')

    rating = models.FloatField(default=.0, verbose_name='Рейтинг')
    reward = models.FloatField(default=.0, verbose_name='KPI к стаб, оплате')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность пользователя поддержки"
        verbose_name_plural = "Сущность пользователя поддержки"
