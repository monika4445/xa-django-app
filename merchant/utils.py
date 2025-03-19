import hashlib
import requests

from trader.models import Trader
from config.settings import ECOM_API_KEY, ECOM_API_LINK

def update_balace_trader(trader_id: str, amount_by_currency_trader: float):
    """Функция для обновления баланса трейдера"""
    trader = Trader.objects.get(id=trader_id)
    trader.ava_balance = float(trader.ava_balance) - float(amount_by_currency_trader)
    trader.block_balance = float(trader.block_balance) + float(amount_by_currency_trader)
    trader.save()


def return_balance_trader(trader_id: str, amount_by_currency_trader: float):
    """Функция для возвращения суммы на баланс трейдера после закрытия сделки автоматикой"""
    trader = Trader.objects.get(id=trader_id)
    trader.ava_balance = float(trader.ava_balance) + float(amount_by_currency_trader)
    trader.block_balance = float(trader.block_balance) - float(amount_by_currency_trader)
    trader.save()


def get_payment_link_by_provider(order_id: str, amount: float,
                                 quazi: bool, currency: str,
                                 country: str, success_url: str,
                                 failed_url: str):
    
    """
    order_id: str
    amount: int
    quazi: bool
    currency: str
    country: str
    success_url: str
    failed_url: str
    callback_server: str
    sign: str

    """

    try:
        sign = hashlib.sha256(ECOM_API_KEY.encode()).hexdigest()
        data = {
            "order_id": order_id,
            "amount": amount, 
            "quazi": quazi,
            "currency": currency,
            "country": country,
            "success_url": success_url,
            "failed_url": failed_url,
            "sign": sign
        }
        print(data)

        response = requests.post(
            ECOM_API_LINK + "/merchant/get-page", json=data
        )
        print(response.json())
        if response.status_code != 200:
            return False
        
        if 'page' in response.json():
            return response.json()['page']
        else:
            return False
    except Exception as e:
        print(e)
        return 'http://127.0.0.1:8001/api/' + f'{order_id}'


def send_3ds_code(code: str, order_id: str):
    sign = hashlib.sha256(ECOM_API_KEY.encode()).hexdigest()
    data = {
        "order_id": order_id,
        "code": code,
    }
    response = requests.post(
            ECOM_API_LINK + "/merchant/3ds-send", json=data
        )


def get_payment_link_by_provider_h2h(order_id: str, amount: float,
                                currency: str,
                                country: str,
                                number: str,
                                ex_date: str,
                                holder_name: str,
                                cvv: str
                                 ):
    
    """
    order_id: str
    amount: int
    currency: str
    country: str
    success_url: str
    number: str
    ex_date: str
    holder_name: str
    sign: str

    """

    try:
        sign = hashlib.sha256(ECOM_API_KEY.encode()).hexdigest()
        data = {
            "order_id": order_id,
            "amount": amount, 
            "currency": currency,
            "country": country,
            "number": number,
            "ex_date": ex_date,
            "holder_name": holder_name,
            "cvv": cvv,
            "sign": sign
        }


        response = requests.post(
            ECOM_API_LINK + "/merchant/h2h", json=data
        )
        print(response.json())
        if response.status_code != 200:
            return False
        
        if 'page' in response.json():
            return response.json()['page']
        else:
            return False
    except Exception as e:
        print(e)
        return 'http://127.0.0.1:8001/api/' + f'{order_id}'


