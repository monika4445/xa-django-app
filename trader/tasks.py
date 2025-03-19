import random
import requests
from celery import shared_task

from merchant.models import Deal, Merchant
from .models import Trader, BaseRateSettings
from accounts.models import TelegramBotSettings


def send_notification_to_webhook(webhook_url: str, 
                                 order_id: str, 
                                 status: str, 
                                 amount: float, 
                                 amount_by_currency_merchant: float, 
                                 rate: float):
    """Функция для отправки нотификации на вебхук мерчанта"""
    data = {
        "id": order_id,
        "status": status,
        "amount": amount,
        "amount_by_currency": amount_by_currency_merchant,
        "rate": rate
    }
    try:
        response = requests.post(webhook_url, json=data)
        print(response.text)
    except Exception as e:
        print(f'Ошибка отправки уведомления по заявке {order_id} - {e}')
        return False

    return True


@shared_task
def send_notification_to_merchant(deal_id: str):
    """Функция для уведомления мерчанта"""
    deal = Deal.objects.get(id=deal_id)
    for _ in range(3):
        send_notification_to_webhook(webhook_url=deal.webhook,
                                    order_id=deal.order_id,
                                    status=deal.status,
                                    amount=deal.amount,
                                    amount_by_currency_merchant=deal.amount_by_currency_merchant,
                                    rate=deal.rate)
    return True


@shared_task
def update_balance_trader_and_merchant(deal_id: str):
    """Функция на обновления данных балансов у трейдера и мерчанта"""

    deal = Deal.objects.get(id=deal_id)

    merchant = Merchant.objects.get(id=deal.source_id.id)
    trader = Trader.objects.get(id=deal.responsible_id.id)

    merchant.balance = float(merchant.balance) + float(deal.amount_by_currency_merchant)
    merchant.save()

    trader.block_balance = float(trader.block_balance) - float(deal.amount_by_currency_trader)
    trader.reward = trader.reward + (float(deal.amount_by_currency) - float(deal.amount_by_currency_trader))
    trader.save()

    # Отправка нотификации на deal.webhook
    send_notification_to_webhook(webhook_url=deal.webhook,
                                 order_id=deal.order_id,
                                 status=deal.status,
                                 amount=deal.amount,
                                 amount_by_currency_merchant=deal.amount_by_currency_merchant,
                                 rate=deal.rate)


@shared_task
def send_telegram_message_trader(trader_id: str, message: str):
    """
    Фоновая функция для отправки сообщения через Telegram Bot API.
    """

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



@shared_task
def update_base_rate_rub_to_usdt(*args):

    method = args[0]
    rate_line = args[1]

    cookies = {
        '_by_l_g_d': 'dac3238f-b21a-3180-65c0-c43b0bd96ecc',
        'bm_sv': '8154FC311C54806A824BFC8177531A96~YAAQlIYUAmZKQdmTAQAAUjdcPxo2jE3NNoI5uDI1J1axbX6ElpZLvBTJ6EQJ/NVW+ED3rXS8TEgTj3XjnHyZWMcJCmLFCrueeuu7sv//Laa6YiboiUWNH7/DJrDfutuwlNSSZM9HwN9aV3xgRYPQW22fiZBAlYdrbunO86AynU/02yiOiqz99A+OHw4FLv/KjD4LCNLxzAH+K7Em5kUGe/B+qHV/wjldzlRkKLPqtEU7DfdthRo/07VnFKneciwK~1',
        '_ga_SPS4ND2MGC': 'GS1.1.1736229717.1.1.1736229733.44.0.0',
        '_fbp': 'fb.1.1736229717923.624986488644034406',
        '_ym_d': '1736229720',
        '_ym_isad': '2',
        '_ym_uid': '1736229720176034632',
        'ak_bmsc': '123415650E36281DF48BF94C9CDA2C00~000000000000000000000000000000~YAAQlIYUAkJ5QNmTAQAArBZbPxr+V13QnLvoJ1WBaDapqNd72+ZAd+zrPGGHDXk0ntkrJ0OCGBFqcodadV6uJ6L2Ck6DPaM15QFJIDfQkeDAAs2VUikP3+dVaR02rOWBZT0/NhBQdmyiMe+Y7Z/Nk31Uw4NpACRFc87s0Q73CShgaCN6i/sNfslvQrd9Ie/qIQZ5ALVT0iAnfBoxyApWqpHR9vzJzzD+knjt1aMnYRbsHS9xDogTACrCUEw6Z19TZCGnE8R6/idRLA6e5UIgr3lcyGAEEWL1Q3mXEq9DrDBk8ed8ahDkXAxfkpGjl0reSQ3kUNJ/ZR6+rs8U0n89KQ/ZCN9Vn262fXU5bO9bR+VZBMAl5YMSssyI1Dr6ySVtVp+W7hV6ShcAbhFZAAVMatv/Z3OdNgNZpcWfGLi+DquiCByPK3/6NzLx7BmBGHYYoB0uWMndPuwPEPLPrUHG42Hq+LDdNOmaVxnIl55d+n6E5N853c6HHC/L8v78UQ==',
        'tmr_lvid': 'e0d3d76060d7300a42b3322248bfa08c',
        'tmr_lvidTS': '1736229719796',
        '_ga': 'GA1.1.2137422071.1736229718',
        '_tt_enable_cookie': '1',
        '_ttp': 'APE-lxoVBWQSSgujNy96mBHHO9K.tt.1',
        '_gcl_au': '1.1.349604894.1736229715',
        'sensorsdata2015jssdkcross': '%7B%22distinct_id%22%3A%221943f5a98c76e6-063488d073be8b-3d626a4b-3686400-1943f5a98c834cb%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C%22_a_u_v%22%3A%220.0.6%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk0M2Y1YTk4Yzc2ZTYtMDYzNDg4ZDA3M2JlOGItM2Q2MjZhNGItMzY4NjQwMC0xOTQzZjVhOThjODM0Y2IifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%7D',
        'bm_mi': 'CAB09EF24810D579DFB415F1544A593E~YAAQlIYUArpwQNmTAQAAlwpbPxpLDzODwR83f9OVocfVknDtXTKQ16tBjDWmg7xvC3T1pwcBx06y5WUqZqUKijVhRCX4TWRoWW2zu+tcJMgkkrEzjGwCcAKOzqyO7OGRJwvK9VikUCCVn8Q1i+r1fIPK1Ld+/eEfgUt+TbHyYaGNzX3Z71e+BMnXnu2VVtmyIO+Xj8xxai0P33iN97pS6KTSTn1DxRizMYLBi7U24GnzimJ0EzA8v+JrZdnrofE2LZ0EHGKBdGmUw+d9oHjQIAOosvQNQ65Dsrm8ixxtHygnYMMMrHIcKhf+eq1qbrORWd8Q31qYpDVwAV6im6Q=~1',
        'bm_sz': '187060B51E142B733905BE16DFB57E1A~YAAQlIYUArxwQNmTAQAAmApbPxqiol7aw8BaS4nzgaBINyRG1sLwjDIA1IboiocT9X9UmAY4nL6TCPzXLEt+AU4M+bqFV+UepviW2FdSbbgCYj87YlV00/xrOrRy1jpA4U1IsxhU0LjPFMMlyHv8cLeBu0/Nzbq92QE8N03aZSpbRlQrs2zzILQQan2TeiF+D5oUIMXPrWYow3ycdeA2C/wkL7J/moSikiPH12KVfGidST6AQ/BnNE7h4MDfdrfj3ksMKIaQgdVxSeK2W1Hmxa/0Wps/6BsiHAC9XabvBnC/gTR75nRDMqY1TA52EPnnYwMOVid+N3t9vS2Cv4+qIP1gBLIfvQyhRsBblKK5VM8BEN8P/KCjOlFBwQO0rqXBYoU7k6bp4RnryTYfByzcd5u8WWvUKPtV~3619120~3617860',
        'detection_time': '1736294400000',
        '_default_mode_token_': '16d26ead-335a-493f-b5bc-e14fd3121449',
        '_general_token_': '426e2001-b984-4e21-9be6-b82d95e163d0',
        '_lax_mode_token_': '4ab1fa73-d0c4-479d-81f7-da5c84f762fd',
        '_none_mode_token_': '9c0ce04e-0072-451b-bfec-d4fe7446f0a6',
        'deviceId': '7727af2d-91ad-b67b-2126-be6fd8042960',
        '_abck': '5FB71D95C1545DE2641CAED86FA553C4~0~YAAQnYYUAkaMMs6TAQAACq5aPw2OT4BZzrjjLhvPYz/87VU3nVtG4CXsWibWE93SJZ9a3qHFZVvLSMM5WEOs3+JXgfd8KOWMhmEYteoXhzy7hkyyEHPNquTtC2aH0sZGeybSNKiFyeNZBKwrAKWYGkodNjgQNPOOhC7fn28z7d7gpXGgHdgJ/TR7xwB1sAIXsjxfO+eWN1YS9BgrSGfLZs25oLFxV77b6KbD/kdysTTQAsmYLReR3TA6m6Mvwsz/0OB/QPxUCm5R+PvgL+60XS6/5TyOEXR8YMIexS9gL60GhVDDLG1BHYCPZhIrVo2lptqrehNorgu0SnPkzO+wI99DTzQJldYceuAJih/qPmI0YRLtk65Mc3Ms8zmG+G2ITlRpKR0lVTAZXTf8buW9nrHRnZudkTzp3d0X8vcWUDnEHUyj2q0smq9V5BgYDY3eM+i7QbkKK6RMLunylJz+cumkCmtup16vyI2AK237ofI=~-1~-1~-1',
        'sajssdk_2015_cross_new_user': '1',
    }

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        # 'Content-Length': '223',
        'Accept': 'application/json',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Site': 'same-site',
        'Host': 'api2.bybit.com',
        'Accept-Language': 'en',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Fetch-Mode': 'cors',
        'Origin': 'https://www.bybit.com',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
        'Referer': 'https://www.bybit.com/',
        # 'Cookie': '_by_l_g_d=dac3238f-b21a-3180-65c0-c43b0bd96ecc; bm_sv=8154FC311C54806A824BFC8177531A96~YAAQlIYUAmZKQdmTAQAAUjdcPxo2jE3NNoI5uDI1J1axbX6ElpZLvBTJ6EQJ/NVW+ED3rXS8TEgTj3XjnHyZWMcJCmLFCrueeuu7sv//Laa6YiboiUWNH7/DJrDfutuwlNSSZM9HwN9aV3xgRYPQW22fiZBAlYdrbunO86AynU/02yiOiqz99A+OHw4FLv/KjD4LCNLxzAH+K7Em5kUGe/B+qHV/wjldzlRkKLPqtEU7DfdthRo/07VnFKneciwK~1; _ga_SPS4ND2MGC=GS1.1.1736229717.1.1.1736229733.44.0.0; _fbp=fb.1.1736229717923.624986488644034406; _ym_d=1736229720; _ym_isad=2; _ym_uid=1736229720176034632; ak_bmsc=123415650E36281DF48BF94C9CDA2C00~000000000000000000000000000000~YAAQlIYUAkJ5QNmTAQAArBZbPxr+V13QnLvoJ1WBaDapqNd72+ZAd+zrPGGHDXk0ntkrJ0OCGBFqcodadV6uJ6L2Ck6DPaM15QFJIDfQkeDAAs2VUikP3+dVaR02rOWBZT0/NhBQdmyiMe+Y7Z/Nk31Uw4NpACRFc87s0Q73CShgaCN6i/sNfslvQrd9Ie/qIQZ5ALVT0iAnfBoxyApWqpHR9vzJzzD+knjt1aMnYRbsHS9xDogTACrCUEw6Z19TZCGnE8R6/idRLA6e5UIgr3lcyGAEEWL1Q3mXEq9DrDBk8ed8ahDkXAxfkpGjl0reSQ3kUNJ/ZR6+rs8U0n89KQ/ZCN9Vn262fXU5bO9bR+VZBMAl5YMSssyI1Dr6ySVtVp+W7hV6ShcAbhFZAAVMatv/Z3OdNgNZpcWfGLi+DquiCByPK3/6NzLx7BmBGHYYoB0uWMndPuwPEPLPrUHG42Hq+LDdNOmaVxnIl55d+n6E5N853c6HHC/L8v78UQ==; tmr_lvid=e0d3d76060d7300a42b3322248bfa08c; tmr_lvidTS=1736229719796; _ga=GA1.1.2137422071.1736229718; _tt_enable_cookie=1; _ttp=APE-lxoVBWQSSgujNy96mBHHO9K.tt.1; _gcl_au=1.1.349604894.1736229715; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%221943f5a98c76e6-063488d073be8b-3d626a4b-3686400-1943f5a98c834cb%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%2C%22_a_u_v%22%3A%220.0.6%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk0M2Y1YTk4Yzc2ZTYtMDYzNDg4ZDA3M2JlOGItM2Q2MjZhNGItMzY4NjQwMC0xOTQzZjVhOThjODM0Y2IifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%7D; bm_mi=CAB09EF24810D579DFB415F1544A593E~YAAQlIYUArpwQNmTAQAAlwpbPxpLDzODwR83f9OVocfVknDtXTKQ16tBjDWmg7xvC3T1pwcBx06y5WUqZqUKijVhRCX4TWRoWW2zu+tcJMgkkrEzjGwCcAKOzqyO7OGRJwvK9VikUCCVn8Q1i+r1fIPK1Ld+/eEfgUt+TbHyYaGNzX3Z71e+BMnXnu2VVtmyIO+Xj8xxai0P33iN97pS6KTSTn1DxRizMYLBi7U24GnzimJ0EzA8v+JrZdnrofE2LZ0EHGKBdGmUw+d9oHjQIAOosvQNQ65Dsrm8ixxtHygnYMMMrHIcKhf+eq1qbrORWd8Q31qYpDVwAV6im6Q=~1; bm_sz=187060B51E142B733905BE16DFB57E1A~YAAQlIYUArxwQNmTAQAAmApbPxqiol7aw8BaS4nzgaBINyRG1sLwjDIA1IboiocT9X9UmAY4nL6TCPzXLEt+AU4M+bqFV+UepviW2FdSbbgCYj87YlV00/xrOrRy1jpA4U1IsxhU0LjPFMMlyHv8cLeBu0/Nzbq92QE8N03aZSpbRlQrs2zzILQQan2TeiF+D5oUIMXPrWYow3ycdeA2C/wkL7J/moSikiPH12KVfGidST6AQ/BnNE7h4MDfdrfj3ksMKIaQgdVxSeK2W1Hmxa/0Wps/6BsiHAC9XabvBnC/gTR75nRDMqY1TA52EPnnYwMOVid+N3t9vS2Cv4+qIP1gBLIfvQyhRsBblKK5VM8BEN8P/KCjOlFBwQO0rqXBYoU7k6bp4RnryTYfByzcd5u8WWvUKPtV~3619120~3617860; detection_time=1736294400000; _default_mode_token_=16d26ead-335a-493f-b5bc-e14fd3121449; _general_token_=426e2001-b984-4e21-9be6-b82d95e163d0; _lax_mode_token_=4ab1fa73-d0c4-479d-81f7-da5c84f762fd; _none_mode_token_=9c0ce04e-0072-451b-bfec-d4fe7446f0a6; deviceId=7727af2d-91ad-b67b-2126-be6fd8042960; _abck=5FB71D95C1545DE2641CAED86FA553C4~0~YAAQnYYUAkaMMs6TAQAACq5aPw2OT4BZzrjjLhvPYz/87VU3nVtG4CXsWibWE93SJZ9a3qHFZVvLSMM5WEOs3+JXgfd8KOWMhmEYteoXhzy7hkyyEHPNquTtC2aH0sZGeybSNKiFyeNZBKwrAKWYGkodNjgQNPOOhC7fn28z7d7gpXGgHdgJ/TR7xwB1sAIXsjxfO+eWN1YS9BgrSGfLZs25oLFxV77b6KbD/kdysTTQAsmYLReR3TA6m6Mvwsz/0OB/QPxUCm5R+PvgL+60XS6/5TyOEXR8YMIexS9gL60GhVDDLG1BHYCPZhIrVo2lptqrehNorgu0SnPkzO+wI99DTzQJldYceuAJih/qPmI0YRLtk65Mc3Ms8zmG+G2ITlRpKR0lVTAZXTf8buW9nrHRnZudkTzp3d0X8vcWUDnEHUyj2q0smq9V5BgYDY3eM+i7QbkKK6RMLunylJz+cumkCmtup16vyI2AK237ofI=~-1~-1~-1; sajssdk_2015_cross_new_user=1',
        'riskToken': 'dmVyMQ|==||==',
        'traceparent': '00-899673e3fc8496b59099a4053d0c1e06-2415bcf6c5b30e21-00',
        'platform': 'PC',
        'guid': 'dac3238f-b21a-3180-65c0-c43b0bd96ecc',
        'lang': 'en',
    }

    json_data = {
        'userId': '',
        'tokenId': 'USDT',
        'currencyId': 'RUB',
        'payment': [
            '382',
        ],
        'side': '0',
        'size': '10',
        'page': '1',
        'amount': '',
        'vaMaker': False,
        'bulkMaker': False,
        'canTrade': False,
        'sortType': 'TRADE_PRICE',
        'paymentPeriod': [],
        'itemRegion': 1,
    }

    response = requests.post('https://api2.bybit.com/fiat/otc/item/online', cookies=cookies, headers=headers, json=json_data)

    if response.status_code != 200:
        return False
    
    data = response.json()
    items = data['result']['items']
    rate_lines = []

    for item in items:
        if int(item['minAmount']) >= 500000:
            rate_lines.append('0')

            if len(rate_line) == rate_line:
                rate = float(item['price'])

                try:
                    rate_settings = BaseRateSettings.objects.get(method=method, county='RUS', currency='RUB')
                except:
                    rate_settings = BaseRateSettings.objects.create(method=method, county='RUS', currency='RUB')
                
                rate_settings.rate = rate
                rate_settings.save()
                return True
    
    return False

