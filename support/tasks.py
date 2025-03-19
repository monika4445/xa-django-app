import uuid
import random
import requests
import json
from celery import shared_task
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from .models import Appeal
from accounts.models import TelegramBotSettings
from trader.models import Trader

@shared_task
def close_appeal(*args):
    """Функция для закрытия аппилки"""
    appeal_id = args[0] 
    appeal = Appeal.objects.get(id=appeal_id)

    appeal.status = Appeal.AppealStatus.EXPIRED
    appeal.save()
    return


def schedule_check_appeal(appeal, deal):
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=int(deal.source_id.sla_on_appeals),
        period=IntervalSchedule.MINUTES,
    )

    PeriodicTask.objects.create(
        interval=schedule,
        name=f"Check Appeal Status {appeal.id}",
        task='support.tasks.close_appeal', 
        args=json.dumps([str(appeal.id)]),
        start_time=deal.created_at,
        one_off=True
    )


@shared_task
def send_telegram_message_trader(*args):
    """
    Фоновая функция для отправки сообщения через Telegram Bot API.
    """

    trader_id: str = args[0]
    message: str = args[1]

    trader = Trader.objects.get(id=trader_id)
    if trader.telegram_id is None:
        return f"Трейдер ID: {trader_id} не имеет telegram id"

    bot_tokens = TelegramBotSettings.objects.filter(notification_type=TelegramBotSettings.NotificationType.TRADER)
    bot_token = random.choice(bot_tokens)

    url = f"https://api.telegram.org/bot{bot_token.bot_token}/sendMessage"
    payload = {
        "chat_id": trader.telegram_id,
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



def schedule_notificatio_appeal_to_trader(deal):
    """Функция для рассылки уведомления трейдеру о созданной аппилке"""
    schedule_1, created = IntervalSchedule.objects.get_or_create(
        every=int(5),
        period=IntervalSchedule.MINUTES,
    )

    schedule_2, created = IntervalSchedule.objects.get_or_create(
        every=int(10),
        period=IntervalSchedule.MINUTES,
    )

    schedule_3, created = IntervalSchedule.objects.get_or_create(
        every=int(deal.source_id.sla_on_appeals) - 5,
        period=IntervalSchedule.MINUTES,
    )

    messages_trader = f"У заказа номер: {deal.order_id} с реквезитом: {deal.creds_id.card_number}, появился спор на сумму, зайдите посмотрите!"

    PeriodicTask.objects.create(
    interval=schedule_1,
    name=f"Notification Appeal by trader {deal.id} - {uuid.uuid4()}",
    task='support.tasks.send_telegram_message_trader', 
    args=json.dumps([str(deal.responsible_id.id), str(messages_trader)]),
    start_time=deal.created_at,
    one_off=True
    )

    PeriodicTask.objects.create(
    interval=schedule_2,
    name=f"Notification Appeal by trader {deal.id} - {uuid.uuid4()}",
    task='support.tasks.send_telegram_message_trader', 
    args=json.dumps([str(deal.responsible_id.id), str(messages_trader)]),
    start_time=deal.created_at,
    one_off=True
    )

    PeriodicTask.objects.create(
    interval=schedule_3,
    name=f"Notification Appeal by trader {deal.id} - {uuid.uuid4()}",
    task='support.tasks.send_telegram_message_trader', 
    args=json.dumps([str(deal.responsible_id.id), str(messages_trader)]),
    start_time=deal.created_at,
    one_off=True
    )