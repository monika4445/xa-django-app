import json
import hashlib
import requests
from celery import shared_task
from django.utils.timezone import now
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from trader.tasks import send_notification_to_webhook

from .models import Deal
from .utils import return_balance_trader
from trader.tasks import send_notification_to_webhook
from config.settings import ECOM_API_KEY, ECOM_API_LINK


@shared_task
def check_and_close_deal(*args):
    try:
        deal_id = args[0] 
        deal = Deal.objects.get(id=deal_id)
        if deal.status == Deal.DealStatus.PENDING:
            deal.status = Deal.DealStatus.CANCELED
            deal.completed_at = now()
            deal.save()
            send_notification_to_webhook(webhook_url=deal.webhook, 
                                 order_id=deal.order_id, 
                                 status=deal.status, 
                                 amount=deal.amount, 
                                 amount_by_currency_merchant=deal.amount_by_currency_merchant, 
                                 rate=deal.rate)
            return_balance_trader(trader_id=deal.responsible_id.id, 
                                  amount_by_currency_trader=deal.amount_by_currency_trader)
            return f"Сделка {deal.order_id} закрыта"
        return f"Сделка {deal.order_id} уже завершена"
    except Deal.DoesNotExist:
        return "Сделка не найдена"


def schedule_check_deal(deal):
    interval_schedule, created = IntervalSchedule.objects.get_or_create(
        every=deal.source_id.sla_on_trade, 
        period=IntervalSchedule.MINUTES  # или MINUTES, если SLA в минутах
    )

    PeriodicTask.objects.create(
        interval=interval_schedule,
        name=f"Check Deal Status {deal.order_id}",
        task='merchant.tasks.check_and_close_deal', 
        args=json.dumps([str(deal.id)]),
        start_time=deal.created_at,
        one_off=True
    )


@shared_task
def check_provider_payment_link_status(deal_id: str):
    """Функция проверки статуса сделки по провайдерской ссылке (ecom)"""

    deal = Deal.objects.get(id=deal_id)
    sign = hashlib.sha256(ECOM_API_KEY.encode()).hexdigest()

    data = {
        "order_id": deal.order_id,
        "sign": sign
    }

    response = requests.post(
        ECOM_API_LINK + '/merchant/cancle-order',
        json=data
    )
    if response.status_code == 200:
        deal.status = Deal.DealStatus.CANCELED
    
    elif response.status_code == 403:
        return
    
    elif response.status_code == 400:
        deal.status = Deal.DealStatus.COMPLETED
    
    send_notification_to_webhook(webhook_url=deal.webhook, 
                                 order_id=deal.order_id, 
                                 status=deal.status, 
                                 amount=deal.amount, 
                                 amount_by_currency_merchant=deal.amount_by_currency_merchant, 
                                 rate=deal.rate)
    deal.save()
    return True


def schedule_check_deal_by_provider_link(deal):
    interval_schedule, created = IntervalSchedule.objects.get_or_create(
        every=deal.source_id.sla_on_trade, 
        period=IntervalSchedule.MINUTES  # или MINUTES, если SLA в минутах
    )

    PeriodicTask.objects.create(
        interval=interval_schedule,
        name=f"Check Deal Status by Provider Link {deal.order_id}",
        task='merchant.tasks.check_provider_payment_link_status', 
        args=json.dumps([str(deal.id)]),
        start_time=deal.created_at,
        one_off=True
    )



@shared_task
def send_telegram_message_system(message: str, topic_type: str):
    """
    Фоновая функция для отправки сообщения через Telegram Bot API.
    """
    topic_ids = {
        "create": '-1002405571117/3',
        "requisite": '-1002405571117/4',
        "payment": '-1002405571117/5'
    }
    bot_token = '7685290161:AAGJ7wA-1zHWkOnaTxuihquKGb2UJTgQYHg'
    chat_id = topic_ids[topic_type]

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке сообщения: {e}")
        return None