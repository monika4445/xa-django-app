from decimal import Decimal
import random
from django.db.models import Q, F, ExpressionWrapper, FloatField
from trader.models import Trader, CredsTrader, PercentSettings, BaseRateSettings, BasePercentSettings
from merchant.models import Deal


def get_random_available_creds(amount_by_currency: float, country: str, currency: str, method: str, amount: str):
    """
    Получает случайный доступный кредс и соответствующего трейдера.

    :param amount: Сумма сделки
    :param country: Страна сделки
    :param currency: Валюта сделки
    :param method: Метод сделки (например, перевод или карта)
    :param bank: Банк сделки
    :return: Словарь с информацией о кредсе и трейдере, либо None если кредсов нет.
    """


    def get_amount_by_currency_new(trader: Trader) -> float:
        percent_setting = PercentSettings.objects.filter(
            user_id=trader,
            country=country,
            currency=currency,
            method=method
        ).first()

        if not percent_setting:
            base_percent_settings = BasePercentSettings.objects.get(
                percent_settings_role=BasePercentSettings.PercentSettingsRole.TRAIDER,
                country=country,
                currency=currency,
                method=method
            )
            percent_setting = PercentSettings.objects.create(
                user_id=trader,
                deposit_percent=base_percent_settings.deposit_percent,
                withdraw_percent=base_percent_settings.withdraw_percent,
                country=country,
                currency=currency,
                method=method
            )

        deposit_percent = percent_setting.deposit_percent
        return amount_by_currency - (amount_by_currency * deposit_percent / 100.0)

    active_traders = Trader.objects.filter(deposit_status=True)

    # Фильтрация трейдеров с учетом достаточного баланса
    eligible_traders = []
    for trader in active_traders:
        amount_by_currency_new = get_amount_by_currency_new(trader)
        if trader.ava_balance > 1000 + amount_by_currency_new:
            eligible_traders.append(trader.id)

    if not eligible_traders:
        return None  # Нет трейдеров с достаточным балансом

    active_creds = CredsTrader.objects.filter(
        status=True,
        user_id__in=eligible_traders,
        country=country,
        currency=currency,
        method=method
    )

    amount = Decimal(str(amount))
    available_creds = active_creds.exclude(
        id__in=Deal.objects.filter(
            Q(status__in=[Deal.DealStatus.PENDING]) &
            Q(creds_id__in=active_creds.values_list("id", flat=True)) &
            Q(amount=amount)
        ).values_list("creds_id", flat=True)
    )

    if available_creds.exists():
        random_creds = random.choice(list(available_creds))
        return {
            "creds_id": random_creds.id,
            "trader_id": random_creds.user_id.id
        }
    else:
        return None

def get_amount_by_currency(amount: float, country: str, currency: str, method: str, mRate: float = None):
    """Функция для расчета суммы по курсу"""
    if mRate:
        rate = Decimal(str(mRate))
        return Decimal(str(amount)) / rate, rate
    
    rate = BaseRateSettings.objects.filter(
        county=country,
        currency=currency,
        method=method,
    ).first()

    if rate:
        return Decimal(str(amount)) / Decimal(str(rate.rate)), Decimal(str(rate.rate))

    return Decimal(str(amount)) / 100, 100
    

