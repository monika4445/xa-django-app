import uuid

from django.db import models


class Trader(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Отправить ботом сделку в тг -> t.me?start=self.id
    telegram_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='ID Telegram')

    user_account = models.ForeignKey(
        "accounts.UserAccounts",
        on_delete=models.CASCADE,
        related_name="trader",
        verbose_name="Аккаунт пользователя"
    )

    referal_id = models.ForeignKey("referal.ReferalUser", on_delete=models.CASCADE, blank=True, null=True, verbose_name='ID реферала')
    
    email = models.CharField(max_length=50, blank=True, null=True, verbose_name='Почта')
    hash_pass = models.CharField(max_length=80, blank=True, null=True, verbose_name='Хеш пароля')

    ava_balance = models.FloatField(default=.00, verbose_name="Актуальный баланс")
    block_balance = models.FloatField(default=.00, verbose_name='Блокированная сумма баланса')

    wallet = models.CharField(max_length=32, blank=True, null=True, verbose_name='Кошелек')

    day_limit = models.IntegerField(default=30, verbose_name='Лимит кол-ва сделок на день')

    admin_status = models.BooleanField(default=False, verbose_name='Апрув админа на трафик')
    deposit_status = models.BooleanField(default=True, verbose_name='Статус депозита')
    withdraw_status = models.BooleanField(default=False, verbose_name='Статус вывода')

    reward = models.FloatField(default=.00, verbose_name='Вознаграждение')

    # убрать
    reward_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID вознаграждения')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность трейдера"
        verbose_name_plural = "Сущность трейдера"

    def save(self, *args, **kwargs):
        if self.ava_balance is not None:
            self.ava_balance = round(self.ava_balance, 6)
        if self.block_balance is not None:
            self.block_balance = round(self.block_balance, 6)
        if self.reward is not None:
            self.reward = round(self.reward, 6)

        super().save(*args, **kwargs)
        

class PercentSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.ForeignKey(Trader, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Трейдер')
    merchant_id = models.ForeignKey("merchant.Merchant", blank=True, null=True, on_delete=models.CASCADE, verbose_name='Мерчант')
    provider_id = models.ForeignKey('Provider', blank=True, null=True, on_delete=models.CASCADE, verbose_name='Провайдер')

    deposit_percent = models.FloatField(default=.0)
    withdraw_percent = models.FloatField(default=.0)

    country = models.CharField(max_length=50, verbose_name='Регион')
    currency = models.CharField(max_length=50, verbose_name='Валюта')
    bank = models.CharField(max_length=255, verbose_name='Банк')

    method = models.CharField(max_length=255, verbose_name='Метод сделок')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность настройки процентажа"
        verbose_name_plural = "Сущность настройки процентажа"



class CredsTrader(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.ForeignKey(Trader, on_delete=models.CASCADE, verbose_name="Трейдер")
    phone_id = models.ForeignKey('TraderPhone', on_delete=models.CASCADE, verbose_name='Телефон трейдера')

    card_number = models.CharField(max_length=16, blank=True, null=True, verbose_name='Номер карты')
    method = models.CharField(max_length=255, verbose_name='Метод сделки')
    bank = models.CharField(max_length=255, blank=True, null=True, verbose_name='Банк карты')
    holder = models.CharField(max_length=255, blank=True, null=True, verbose_name='Инициалы держателя карты')
    status = models.BooleanField(default=False, verbose_name='Активно?')

    max_op = models.IntegerField(default=10, verbose_name='Максимальное кол-во сделок в один момент')

    country = models.CharField(max_length=50, verbose_name='Регион')
    currency = models.CharField(max_length=50, verbose_name='Валюта')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность данных карт трейдера"
        verbose_name_plural = "Сущность данных карт трейдера"


class TraderPhone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.ForeignKey(Trader, on_delete=models.CASCADE, verbose_name='Трейдер')

    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Название')
    status = models.BooleanField(default=False, verbose_name='Устройство активно?')
    is_online = models.BooleanField(default=False, verbose_name='Устройство онлайн?')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность телефона трейдера"
        verbose_name_plural = "Сущность телефона трейдера"

   
class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=100, blank=True, null=True, verbose_name="Название")
    status = models.BooleanField(default=False, verbose_name='Активно?')

    total_raward = models.FloatField(default=.00, verbose_name='Общее кол-во вознаграждений в группе')

    include_self = models.BooleanField(default=False, verbose_name='Наши трейдеры?')
    self_limit = models.IntegerField(verbose_name='Суточный лимит на наших трейдеров')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность группы"
        verbose_name_plural = "Сущность группы"


class Provider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    group_id = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Группа')

    provider_params = models.JSONField(verbose_name="Параметры запроса", blank=True, null=True)
    status = models.BooleanField(default=False, verbose_name='Активно?')
    day_limit = models.IntegerField(verbose_name='Дневной лимит')

    deposit_status = models.BooleanField(default=False, verbose_name='Статус депозита')
    withdraw_status = models.BooleanField(default=False, verbose_name='Статус вывода')

    referal_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='ID реферала')

    min_dep_amount = models.FloatField(default=.00, verbose_name="Минимальный депозит")
    max_dep_amount = models.FloatField(default=.00, verbose_name="Максимальный депозит")

    max_with_amount = models.FloatField(default=.00, verbose_name='Максимальный вывод')
    min_with_amount = models.FloatField(default=.00, verbose_name='Минимальный вывод')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность провайдера"
        verbose_name_plural = "Сущность провайдера"


class BasePercentSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class PercentSettingsRole(models.TextChoices):
        PROVIDER = 'PROVIDER'
        MERCHANT = 'MERCHANT'
        TRAIDER = 'TRAIDER'
    percent_settings_role = models.CharField(max_length=50, choices=PercentSettingsRole.choices, verbose_name="Для кого настройка?")

    deposit_percent = models.FloatField(default=.0, verbose_name='Процент с депозита')
    withdraw_percent = models.FloatField(default=.0, verbose_name='Процент с вывода')

    country = models.CharField(max_length=255, verbose_name='Регион')
    currency = models.CharField(max_length=255, verbose_name='Валюта')
    method = models.CharField(max_length=255, verbose_name='Метод')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность базовой настройки процентов"
        verbose_name_plural = "Сущность базовой настройки процентов"
    
    def __str__(self) -> str:
        return f"{self.percent_settings_role} - {self.country} - {self.currency} - ({self.method})"


class BaseRateSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    rate = models.FloatField(default=.00, verbose_name='Курс')
    bank = models.CharField(max_length=255, blank=True, null=True, verbose_name='Банк')

    county = models.CharField(max_length=255, verbose_name='Страна')
    currency = models.CharField(max_length=255, verbose_name='Валюта')

    method = models.CharField(max_length=255, blank=True, null=True, verbose_name='Способ')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность курса валют на USDT"
        verbose_name_plural = "Сущность курса валют на USDT"