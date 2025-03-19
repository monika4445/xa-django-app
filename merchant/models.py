import uuid
import hashlib
from django.db import models
from decimal import Decimal

from config import settings

from trader.models import BaseRateSettings, PercentSettings, BasePercentSettings
from .utils import update_balace_trader


class Merchant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_account = models.ForeignKey(
        "accounts.UserAccounts",
        on_delete=models.CASCADE,
        related_name="merchant",
        verbose_name="Аккаунт пользователя",
        blank=True, null=True
    )

    group_id = models.ForeignKey("trader.Group", blank=True, null=True, on_delete=models.CASCADE, verbose_name='Группа')
    referal_id = models.ForeignKey("referal.ReferalUser", blank=True, null=True, on_delete=models.CASCADE, verbose_name='ID реферала')

    title = models.CharField(max_length=255, blank=True, null=True, verbose_name="Название")
    balance = models.FloatField(default=.00, verbose_name='Баланс')
    hash_api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name='API KEY')

    status = models.BooleanField(default=False, verbose_name='Активно?')

    total_settl = models.FloatField(default=.0, verbose_name='Сколько было выводов')

    sla_on_trade = models.IntegerField(default=15, verbose_name='Минуты на оплату')
    sla_on_appeals = models.IntegerField(default=30, verbose_name='Минуты на решение спора')

    max_amount_sla = models.IntegerField(default=150, verbose_name='Максимальная сумма в $ в которой закрывается спор без ответа')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность мерчанта"
        verbose_name_plural = "Сущность мерчанта"
    
    def save(self, *args, **kwargs):
        if not self.hash_api_key:
            data = f"{self.id}:{settings.SECRET_KEY}".encode('utf-8')
            self.hash_api_key = hashlib.sha256(data).hexdigest()
        if self.balance is not None:
            self.balance = round(self.balance, 6)

        super().save(*args, **kwargs)
          


class Deal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order_id = models.CharField(max_length=255, unique=True)

    provider_invoice_id = models.CharField(max_length=255, blank=True, null=True)
    provider_id = models.ForeignKey("trader.Provider", blank=True, null=True, on_delete=models.CASCADE, verbose_name='Провайдер')

    responsible_id = models.ForeignKey("trader.Trader", blank=True, null=True, on_delete=models.CASCADE, verbose_name='Трейдер')
    creds_id = models.ForeignKey('trader.CredsTrader', blank=True, null=True, on_delete=models.CASCADE, verbose_name='Креды трейдера')

    amount = models.DecimalField(max_digits=10, decimal_places=2) 

    amount_by_currency = models.DecimalField(max_digits=10, decimal_places=2) 

    amount_by_currency_merchant = models.DecimalField(max_digits=10, decimal_places=2)
    amount_by_currency_trader = models.DecimalField(max_digits=10, decimal_places=2)
    amount_by_currency_provider = models.DecimalField(max_digits=10, decimal_places=2) 


    method = models.CharField(max_length=255)

    county = models.CharField(max_length=255, verbose_name='Страна')
    currency = models.CharField(max_length=255, verbose_name='Валюта')

    webhook = models.CharField(max_length=255, verbose_name='URL уведомлений')
    
    # Withdraw
    holder_name_rec = models.CharField(max_length=255)
    number_rec = models.CharField(max_length=255, blank=True, null=True)
    bank = models.CharField(max_length=255)

    class DealStatus(models.TextChoices):
        PENDING = 'pending'
        COMPLETED = 'confirmed'
        EXPIRED = 'expired'
        DISPUTE = 'dispute'
        CANCELED = 'canceled'
    status = models.CharField(max_length=50, choices=DealStatus.choices, default=DealStatus.PENDING)

    class DealType(models.TextChoices):
        DEPOSIT = 'deposit'
        WITHDRAW = 'withdraw'
    type = models.CharField(max_length=50, choices=DealType.choices)

    rate = models.FloatField(default=.00, verbose_name='Курс')
    
    # Вывод средств
    decode_holder_name_client = models.CharField(max_length=255, blank=True, null=True)
    decode_number_client = models.CharField(max_length=255, blank=True, null=True)
    decode_bank_client = models.CharField(max_length=255, blank=True, null=True)

    # ecom
    decode_expiration_date_card_client = models.DateField(blank=True, null=True)
    decode_cvv_client = models.CharField(max_length=4, blank=True, null=True)
    
    completed_at = models.DateTimeField(blank=True, null=True)

    source_id = models.ForeignKey(Merchant, on_delete=models.CASCADE, verbose_name='Мерчант')
    client_id = models.ForeignKey("Client", blank=True, null=True, on_delete=models.CASCADE, verbose_name='Клиент')

    media_key = models.CharField(max_length=255, blank=True, null=True, verbose_name='Ссылка на S3')

    success_url = models.CharField(max_length=255, blank=True, null=True, verbose_name='Редирект при успешной оплате ECOM')
    failed_url = models.CharField(max_length=255, blank=True, null=True, verbose_name='Редирект при ошибки оплаты ECOM')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность сделки"
        verbose_name_plural = "Сущность сделки"

    def __str__(self):
        return self.order_id

    def deposit_deal_save(self, *args, **kwargs):
        if Decimal(str(self.amount_by_currency_merchant)) == Decimal(str(1.0)):
            try:
                percent_settings_merchant = PercentSettings.objects.get(merchant_id=self.source_id)
            except:
                base_percent_settings = BasePercentSettings.objects.get(percent_settings_role=BasePercentSettings.PercentSettingsRole.MERCHANT, 
                                                                        country=self.county,
                                                                        currency=self.currency,
                                                                        method=self.method)

                percent_settings_merchant = PercentSettings.objects.create(merchant_id=self.source_id, 
                                                                            country=self.county,
                                                                            currency=self.currency,
                                                                            deposit_percent=base_percent_settings.deposit_percent,
                                                                            withdraw_percent=base_percent_settings.withdraw_percent,
                                                                            method=self.method)
                
            self.amount_by_currency_merchant = Decimal(str(self.amount_by_currency)) - Decimal(str(Decimal(str(percent_settings_merchant.deposit_percent)) / Decimal(str(100.0)) * Decimal(str(self.amount_by_currency))))

        if self.responsible_id:
            percent_settings_trader = PercentSettings.objects.filter(user_id=self.responsible_id,
                                                                    country=self.county,
                                                                    currency=self.currency,
                                                                    method=self.method).first()

            self.amount_by_currency_trader = Decimal(str(self.amount_by_currency)) - Decimal(str(Decimal(str(percent_settings_trader.deposit_percent)) / Decimal(str(100.0)) * Decimal(str(self.amount_by_currency))))
            update_balace_trader(self.responsible_id.id, self.amount_by_currency_trader)

        super().save(*args, **kwargs)


    def withdraw_deal_save(self, *args, **kwargs):
        if Decimal(str(self.amount_by_currency_merchant)) == Decimal(str(1.0)):
            try:
                percent_settings_merchant = PercentSettings.objects.get(merchant_id=self.source_id)
            except:
                base_percent_settings = BasePercentSettings.objects.get(percent_settings_role=BasePercentSettings.PercentSettingsRole.MERCHANT, 
                                                                        country=self.county,
                                                                        currency=self.currency,
                                                                        method=self.method)

                percent_settings_merchant = PercentSettings.objects.create(merchant_id=self.source_id, 
                                                                            country=self.county,
                                                                            currency=self.currency,
                                                                            deposit_percent=base_percent_settings.deposit_percent,
                                                                            withdraw_percent=base_percent_settings.withdraw_percent,
                                                                            method=self.method)
                
            self.amount_by_currency_merchant = Decimal(str(self.amount_by_currency)) - Decimal(str(Decimal(str(percent_settings_merchant.withdraw_percent)) / Decimal(str(100.0)) * Decimal(str(self.amount_by_currency))))

        if self.responsible_id:
            percent_settings_trader = PercentSettings.objects.filter(user_id=self.responsible_id,
                                                                    country=self.county,
                                                                    currency=self.currency,
                                                                    method=self.method).first()
            
            if not percent_settings_trader:
                base_percent_settings = BasePercentSettings.objects.get(percent_settings_role=BasePercentSettings.PercentSettingsRole.TRAIDER, 
                                                                        country=self.county,
                                                                        currency=self.currency,
                                                                        method=self.method)

                percent_settings_trader = PercentSettings.objects.create(user_id=self.responsible_id, 
                                                                            country=self.county,
                                                                            currency=self.currency,
                                                                            deposit_percent=base_percent_settings.deposit_percent,
                                                                            withdraw_percent=base_percent_settings.withdraw_percent,
                                                                            method=self.method)
                

            self.amount_by_currency_trader = Decimal(str(self.amount_by_currency)) - Decimal(str(Decimal(str(percent_settings_trader.withdraw_percent)) / Decimal(str(100.0)) * Decimal(str(self.amount_by_currency))))

        super().save(*args, **kwargs)        


class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    id_client = models.CharField(max_length=255, verbose_name='ID клиета от мерчанта')
    email = models.CharField(max_length=255, verbose_name='Почта')

    first_name = models.CharField(max_length=255, verbose_name='Имя')
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Фамилия')

    ip = models.CharField(max_length=50, verbose_name='IP адресс')
    billing_addres = models.CharField(max_length=100, blank=True, null=True, verbose_name='Физический адресс проживания')

    phone_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='Номер телефона')
    ban = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность клиента"
        verbose_name_plural = "Сущность клиента"


class SubMerchantAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    merchant_user = models.ForeignKey(Merchant, on_delete=models.CASCADE, verbose_name='Аккаунт мерчанта')
    user_account = models.ForeignKey(
        "accounts.UserAccounts",
        on_delete=models.CASCADE,
        related_name="sub_merchant",
        verbose_name="Аккаунт пользователя",
        blank=True, null=True
    )

    class SubMerchantRole(models.TextChoices):
        SUPPORT = 'SUPPORT'
        BOOKER = 'BOOKER'
    role = models.CharField(max_length=50, choices=SubMerchantRole.choices, verbose_name='Роль суб. аккаунта мерча')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сущность суб. аккаунта мерча"
        verbose_name_plural = "Сущность суб. аккаунта мерча"