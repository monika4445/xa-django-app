from django.contrib.auth.models import update_last_login
from decimal import Decimal
from drf_yasg import openapi
from datetime import datetime, timedelta
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from utils import BaseCRUD, CustomPagination
from .models import (
    Merchant, Deal, Client, SubMerchantAccount
)
from merchant.serializer import (
    MerchantSerialzier, 
    MerchantRequestDepositSerialzier, MerchantResponseDepositSerialzier,
    MerchantWithdrawRequestSeraialzier, MerchantWithdrawResponseSerialzier,
    EcomCreateDealSerializer, EcomResponseDealSerializer,
    SubMerchantAccauntSerialzier, SubMerchantAccountCreateSerialzier,
    MerchantTrafficSerializer, EcomInteranlConfirmSerialzier,
    EcomInteranlConfirmResponseSerialzier,
    EcomCreateDealSerializerH2H as EcomCreateDealH2HSerializer,
    ThreeDSCodeResponseSerializer,
    ThreeDSCodeSerializer,
)
from accounts.models import UserAccounts
from trader.models import Trader, CredsTrader, PercentSettings, BaseRateSettings
from trader.utils import get_random_available_creds, get_amount_by_currency
from .tasks import schedule_check_deal, schedule_check_deal_by_provider_link, send_telegram_message_system
from trader.tasks import send_telegram_message_trader
from .utils import get_payment_link_by_provider, get_payment_link_by_provider_h2h, send_3ds_code
from trader.tasks import send_notification_to_webhook


class UserBaseViewSet(BaseCRUD):
    permission_classes = [AllowAny]
    serializer_class = MerchantSerialzier
    pagination_class = CustomPagination

    _model = Merchant
    _serializer = serializer_class

    @swagger_auto_schema(
        responses={200: MerchantSerialzier, 400: 'Bad Request'},
        operation_summary="Get info Merchant User Account",
        operation_description="This endpoint geting info merchant user account.",
        tags=["MERCHANT"]
    )
    def me(self, request):
        try:
            user = UserAccounts.objects.get(id=request.user.id)
        except:
            return Response({"message": "This user not found system"}, 404)

        try:
            trader = Merchant.objects.get(user_account=user)
        except:
            return Response({'message': "This user not found merchant obj."}, 400)
        
        serialzier = self._serializer(trader)
        return Response(serialzier.data)


class MerchantDepositViewSet(BaseCRUD):
    permission_classes = [IsAuthenticated]
    serializer_class = MerchantResponseDepositSerialzier
    pagination_class = CustomPagination

    _model = Merchant
    _serializer = serializer_class
    _serializer_create = MerchantRequestDepositSerialzier

    @swagger_auto_schema(
        request_body=MerchantRequestDepositSerialzier,
        responses={200: MerchantResponseDepositSerialzier, 400: 'Bad Request'},
        operation_summary="Create deposit request to Merchant User Account",
        operation_description="This endpoint create deposit request to info merchant user account.",
        tags=["MERCHANT"]
    )
    def create(self, request):
        try:
            merchant = Merchant.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not merchant role'}, 400)

        serialzier = self._serializer_create(data=request.data)
        if serialzier.is_valid():
            
            amount_by_currency, rate = get_amount_by_currency(amount=float(serialzier.data['amount']),
                                                        country=serialzier.data['county'],
                                                        currency=serialzier.data['currency'],
                                                        method=serialzier.data['method'],
                                                        mRate=serialzier.data['mRate'] if 'mRate' in serialzier.data 
                                                                                        and Decimal(str(serialzier.data['mRate'])) != Decimal(str(0.0))
                                                                                          else None)
            
            active_creds = get_random_available_creds(amount_by_currency=float(amount_by_currency),
                                                      country=serialzier.data['county'],
                                                      currency=serialzier.data['currency'],
                                                      method=serialzier.data['method'],
                                                      amount=serialzier.data['amount']) 
            if active_creds is None:
                # Отправляем системное уведомление
                message = f"Реквизит не найден! Сумма: {serialzier.data['amount']} {serialzier.data['currency']}. Мерч: {merchant.title}"
                send_telegram_message_system.delay(message, topic_type='requisite')

                return Response({'message': 'This not active trader creds'}, 400)

            active_creds_obj = CredsTrader.objects.get(id=active_creds['creds_id'])

            if serialzier.data['county'] == 'RUS' and serialzier.data['currency'] == 'RUB':
                    client = None
            else:
                if 'client' in serialzier.data:
                    client = Client.objects.create(
                        id_client=serialzier.data['client']['id'],
                        email=serialzier.data['client']['email'],
                        phone_number=serialzier.data['client']['phone_number'] if 'phone_number' in serialzier.data['client'] else '',
                        first_name=serialzier.data['client']['first_name'],
                        last_name=serialzier.data['client']['last_name']
                    )
                else:
                    client = None
            
            deal = Deal.objects.create(
                order_id=serialzier.data['id'],
                county=serialzier.data['county'],
                currency=serialzier.data['currency'],
                webhook=serialzier.data['webhook'],
                amount=serialzier.data['amount'],
                amount_by_currency=amount_by_currency,
                amount_by_currency_merchant=1,
                amount_by_currency_trader=1,
                amount_by_currency_provider=1,
                type=Deal.DealType.DEPOSIT,
                method=serialzier.data['method'],
                rate=rate,
                source_id=merchant,
                client_id=client,
                creds_id=active_creds_obj,
                responsible_id=active_creds_obj.user_id
            )
            deal.deposit_deal_save()

            serialzier_response = dict(
                id=deal.order_id,
                invoice_id=deal.id,
                amount=deal.amount,
                amount_by_currency=deal.amount_by_currency_merchant, 
                rate=deal.rate,
                requisite=dict(number=active_creds_obj.card_number,
                               holder_name=active_creds_obj.holder,
                               bank=active_creds_obj.bank)
            )

            schedule_check_deal(deal=deal)

            # Отправляем трейдеру уведомление
            message_trader = f"Создана сделка! Сумма: {deal.amount} {serialzier.data['currency']}. Выдан реквезит: {active_creds_obj.card_number}"
            send_telegram_message_trader.delay(deal.responsible_id.id, message_trader)

            # Отправляем системное уведомление
            message = f"Создана сделка! Сумма: {deal.amount} {deal.currency}. Выдан реквезит: {active_creds_obj.card_number}. Трейдер: {active_creds_obj.user_id.login}. Мерч: {merchant.title}"
            send_telegram_message_system.delay(message, topic_type='create')

            return Response(serialzier_response, 200)
        else:
            return Response(serialzier.errors, 400)
            

class MerchantWithdrawViewSet(BaseCRUD):
    permission_classes = [IsAuthenticated]
    serializer_class = MerchantWithdrawResponseSerialzier
    pagination_class = CustomPagination

    _model = Merchant
    _serializer = serializer_class
    _serializer_create = MerchantWithdrawRequestSeraialzier

    @swagger_auto_schema(
        request_body=MerchantWithdrawRequestSeraialzier,
        responses={200: MerchantWithdrawResponseSerialzier, 400: 'Bad Request'},
        operation_summary="Create withdraw request to Merchant User Account",
        operation_description="This endpoint create withdraw request to info merchant user account.",
        tags=["MERCHANT"]
    )
    def create(self, request):
        try:
            merchant = Merchant.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not merchant role'}, 400)
        
        serialzier = self._serializer_create(data=request.data)
        if serialzier.is_valid():
            
            amount_by_currency, rate = get_amount_by_currency(amount=float(serialzier.data['amount']),
                                                        country=serialzier.data['county'],
                                                        currency=serialzier.data['currency'],
                                                        method=serialzier.data['method'],
                                                        mRate=serialzier.data['mRate'] if 'mRate' in serialzier.data 
                                                                                        and Decimal(str(serialzier.data['mRate'])) != Decimal(str(0.0))
                                                                                          else None)

            try:
                client = Client.objects.get(id_client=serialzier.data['client']['id'])
            except:
                client = Client.objects.create(
                    id_client=serialzier.data['client']['id'],
                    first_name=serialzier.data['client']['first_name'],
                    last_name=serialzier.data['client']['last_name'],
                    phone_number=serialzier.data['client']['phone_number'],
                    email=serialzier.data['client']['email']
                )
                

            deal = Deal.objects.create(
                order_id=serialzier.data['id'],
                county=serialzier.data['county'],
                currency=serialzier.data['currency'],
                amount=serialzier.data['amount'],
                webhook=serialzier.data['webhook'],
                amount_by_currency=amount_by_currency,
                amount_by_currency_merchant=1,
                amount_by_currency_trader=1,
                amount_by_currency_provider=1,
                method=serialzier.data['method'],
                status=Deal.DealStatus.PENDING,
                type=Deal.DealType.WITHDRAW,
                number_rec=serialzier.data['requisite']['number'],
                holder_name_rec=serialzier.data['requisite']['holder_name'],
                bank=serialzier.data['requisite']['bank'],
                source_id=merchant,
                client_id=client,
                rate=rate
            )
            deal.withdraw_deal_save()


            serialzier_response = dict(
                id=deal.order_id,
                invoice_id=deal.id,
                amount=deal.amount,
                amount_by_currency=deal.amount_by_currency_merchant,
                rate=deal.rate
            )
            return Response(serialzier_response)
        else:
            return Response(serialzier.errors, 400)



class EcomDealViewSet(BaseCRUD):
    permission_classes = [IsAuthenticated]
    serializer_class = EcomResponseDealSerializer
    pagination_class = CustomPagination

    _model = Deal
    _serializer = serializer_class
    _serializer_create = EcomCreateDealSerializer

    @swagger_auto_schema(
        request_body=EcomCreateDealSerializer,
        responses={200: EcomResponseDealSerializer, 400: 'Bad Request'},
        operation_summary="Create ecom request to Merchant User Account",
        operation_description="This endpoint create ecom request to merchant user account.",
        tags=["ECOM"]
    )
    def create(self, request):
        """метод для создания ecom сделки"""
        try:
            merchant = Merchant.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not a have role merchant'})

        serialzier = self._serializer_create(data=request.data)
        if serialzier.is_valid():

            payment_page = get_payment_link_by_provider(order_id=serialzier.data['id'],
                                                        amount=serialzier.data['amount'],
                                                        quazi=True,
                                                        currency='RUB',
                                                        country='RUS',
                                                        success_url=serialzier.data['success_url'],
                                                        failed_url=serialzier.data['failed_url'])

            amount_by_currency, rate = get_amount_by_currency(amount=float(serialzier.data['amount']),
                                                        country='RUS',
                                                        currency='RUB',
                                                        method='ecom')

            deal = Deal.objects.create(
                order_id=serialzier.data['id'],
                county='RUS',
                currency='RUB',
                webhook=serialzier.data['webhook'],
                amount=serialzier.data['amount'],
                amount_by_currency=amount_by_currency,
                amount_by_currency_merchant=1,
                amount_by_currency_trader=1,
                amount_by_currency_provider=1,
                type=Deal.DealType.DEPOSIT,
                method='ecom',
                rate=rate,
                source_id=merchant,
                success_url=serialzier.data['success_url'],
                failed_url=serialzier.data['failed_url']
            )
            deal.deposit_deal_save()
            

            serialzier_response = dict(
                id=deal.order_id,
                invoice_id=deal.id,
                amount=deal.amount,
                amount_by_currency=deal.amount_by_currency_merchant, 
                rate=deal.rate,
                payment_link=payment_page
            )
            schedule_check_deal_by_provider_link(deal=deal)
            
            return Response(serialzier_response, 200)
        else:
            return Response(serialzier.errors, 400)


class CreateOrderViewH2H(BaseCRUD):
    """
    API endpoint для создания ecom сделки
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EcomCreateDealH2HSerializer
    pagination_class = CustomPagination

    _model = Deal
    _serializer = serializer_class
    _serializer_create = EcomCreateDealH2HSerializer
    @swagger_auto_schema(
        request_body=EcomCreateDealH2HSerializer,
        responses={200: EcomResponseDealSerializer, 400: "Bad Request"},
        operation_summary="Create ecom order h2h",
        operation_description="This endpoint creates an ecom order for a merchant account.",
        tags=["ECOM"],
    )
    def create(self, request):
        print(request.data)
        """
        Создание ecom заказа для указанного мерчанта
        """
        try:
            merchant = Merchant.objects.get(user_account=request.user)
        except Merchant.DoesNotExist:
            return Response(
                {"message": "This user does not have the role of merchant"},
                200
            )
        serializer = EcomCreateDealH2HSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            print(data)

            # Генерация ссылки на оплату через провайдера
            get_payment_link_by_provider_h2h(
                order_id=data["id"],
                amount=data["amount"],
                currency="RUB",
                country="RUS",
                number=data["requisite"]["number"],
                ex_date=data["requisite"]["ex_date"],
                cvv=data["requisite"]["cvv"],
                holder_name=data["requisite"]["holder_name"],
            )

            # Вычисление суммы в валюте и курса
            amount_by_currency, rate = get_amount_by_currency(
                amount=float(data["amount"]),
                country="RUS",
                currency="RUB",
                method="ecom",
            )

            # Создание записи в базе данных
            deal = Deal.objects.create(
                order_id=data["id"],
                county="RUS",
                currency="RUB",
                webhook=data["webhook"],
                amount=data["amount"],
                amount_by_currency=amount_by_currency,
                amount_by_currency_merchant=1,  # Для заполнения позже
                amount_by_currency_trader=1,  # Для заполнения позже
                amount_by_currency_provider=1,  # Для заполнения позже
                type=Deal.DealType.DEPOSIT,
                method="ecom",
                rate=rate,
                source_id=merchant,
                success_url=data["success_url"],
                failed_url=data["failed_url"],
            )
            deal.deposit_deal_save()

            # Формирование ответа
            response_data = {
                "id": deal.order_id,
                "invoice_id": deal.id,
                "amount": deal.amount,
                "amount_by_currency": deal.amount_by_currency_merchant,
                "rate": deal.rate,
                "payment_link": False,
            }

            # Планирование проверки состояния сделки
            schedule_check_deal_by_provider_link(deal=deal)

            return Response(response_data, status=200)

        return Response(serializer.errors, status=500)


class Send3DSCodeViewSet(BaseCRUD):
    """
    API endpoint для создания ecom сделки
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ThreeDSCodeResponseSerializer
    pagination_class = CustomPagination

    _model = Deal
    _serializer = serializer_class
    _serializer_create = ThreeDSCodeSerializer
    @swagger_auto_schema(
        request_body=ThreeDSCodeSerializer,
        responses={200: ThreeDSCodeResponseSerializer, 400: "Bad Request"},
        operation_summary="Create ecom order h2h",
        operation_description="This endpoint creates an ecom order for a merchant account.",
        tags=["ECOM"],
    )
    def create(self, request):
        print(request.data)
        """
        Создание ecom заказа для указанного мерчанта
        """
        try:
            merchant = Merchant.objects.get(user_account=request.user)
        except Merchant.DoesNotExist:
            return Response(
                {"message": "This user does not have the role of merchant"},
                200
            )
        serializer = ThreeDSCodeSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            # Генерация ссылки на оплату через провайдера
            
            send_3ds_code(data["code"], data["id"])
            # Создание записи в базе данных
            deal = Deal.objects.get(order_id=data["id"])
            deal.status = Deal.DealStatus.COMPLETED
            deal.save()

            # Формирование ответа
            response_data = {
                	"id": deal.order_id,
	                "status": True
            }

            return Response(response_data, status=200)

        return Response(serializer.errors, status=500)


class EcomInternalComfirmViewSet(BaseCRUD):
    permission_classes = [AllowAny]
    serializer_class = EcomInteranlConfirmResponseSerialzier
    pagination_class = CustomPagination

    _model = Deal
    _serializer = serializer_class
    _serializer_create = EcomInteranlConfirmSerialzier

    @swagger_auto_schema(
        request_body=EcomInteranlConfirmSerialzier,
        responses={200: EcomInteranlConfirmResponseSerialzier, 400: 'Bad Request'},
        operation_summary="Webhook ecom comfirm request to Merchant User Account",
        operation_description="This endpoint Webhook ecom comfirm request to merchant user account.",
        tags=["ECOM"]
    )
    def internal_confirm(self, request):
        """метод для получения уведомления о успешном закрытии сделки"""
        serializer = EcomInteranlConfirmSerialzier(data=request.data)
        if serializer.is_valid():
            order_id = serializer.data['order_id']
            deal = Deal.objects.get(order_id=order_id)
            deal.status = Deal.DealStatus.COMPLETED
            deal.save()

            merchant = Merchant.objects.get(id=deal.source_id.id)
            merchant.balance = float(merchant.balance) + float(deal.amount_by_currency_merchant)
            merchant.save()
            send_notification_to_webhook(webhook_url=deal.webhook, 
                                 order_id=deal.order_id, 
                                 status=deal.status, 
                                 amount=deal.amount, 
                                 amount_by_currency_merchant=deal.amount_by_currency_merchant, 
                                 rate=deal.rate)

            return Response({"message": 'OK'}, 200)
        else:
            return Response(serializer.errors, 400)
        

class SubMerchantAccountViewSet(BaseCRUD):
    permission_classes = [IsAuthenticated]
    serializer_class = SubMerchantAccauntSerialzier
    pagination_class = CustomPagination

    _model = SubMerchantAccount
    _serializer = serializer_class
    _serializer_create = SubMerchantAccountCreateSerialzier

    @swagger_auto_schema(
        request_body=SubMerchantAccountCreateSerialzier,
        responses={200: SubMerchantAccauntSerialzier, 400: 'Bad Request'},
        operation_summary="Create Sub Account merchant user",
        operation_description="This endpoint create Sub Account merchant user.",
        tags=["MERCHANT"]
    )
    def create(self, request):
        try:
            merchant = Merchant.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not have a merchant role'}, 400)

        serializer = self._serializer_create(data=request.data)
        if serializer.is_valid():
            if not serializer.data['role'] in SubMerchantAccount.SubMerchantRole:
                return Response({"message": 'This role not found system'}, 400)

            user = UserAccounts.objects.create_user(
                login=serializer.data['email'],
                password=serializer.data['password']
            )
            user.is_active = True
            user.is_confirmed = True
            user.in_consideration = True
            user.save()

            sub_account = SubMerchantAccount.objects.create(
                merchant_user=merchant,
                user_account=user,
                role=serializer.data['role']
            )

            serialzier_obj = self._serializer(sub_account).data
            return Response(serialzier_obj, 200)
        else:
            return Response(serializer.errors, 400)

    @swagger_auto_schema(
        responses={200: SubMerchantAccauntSerialzier, 400: 'Bad Request'},
        operation_summary="Get Sub Account merchant user",
        operation_description="This endpoint get Sub Account merchant user.",
        tags=["MERCHANT"]
    )
    def sub_account_me(self, request):
        try:
            sub_account = SubMerchantAccount.objects.get(user_account=request.user)
        except:
            return Response({"message": 'This user not sub. account merchant'}, 400)
        
        seriazlier = self._serializer(sub_account).data
        return Response(seriazlier, 200)


class ThreadDealsViewSet(BaseCRUD):
    permission_classes = [IsAuthenticated]
    serializer_class = MerchantTrafficSerializer
    pagination_class = CustomPagination

    _model = Deal
    _serializer = serializer_class

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'days',
                openapi.IN_QUERY,
                description="Временная дельта в днях",
                type=openapi.TYPE_INTEGER,
                default=7
            )
        ],
        responses={200: MerchantTrafficSerializer, 400: 'Bad Request'},
        operation_summary="Получение информации о потоках трафика",
        operation_description="Возвращает данные о сделках и процентных настройках по мерчанту",
        tags=["TRAFFIC"]
    )
    def traffic(self, request):
        try:
            merchant_id = Merchant.objects.get(user_account=request.user)
        except:
            try:
                sub_account = SubMerchantAccount.objects.get(user_account=request.user)
                merchant_id = sub_account.merchant_user
            except:
                return Response({"message": 'This user not a have role merchant'}, 400)

        try:
            delta_days = int(request.query_params.get('days', 7))
            date_from = datetime.now() - timedelta(days=delta_days)

            percent_settings = PercentSettings.objects.filter(merchant_id=merchant_id)

            if not percent_settings.exists():
                return Response({"message": "No PercentSettings found for the given merchant"}, 404)

            grouped_data = {}

            for setting in percent_settings:
                deals = Deal.objects.filter(
                    source_id=merchant_id,
                    created_at__gte=date_from,
                    county=setting.country,
                    currency=setting.currency,
                    method=setting.method,
                )

                if setting.country not in grouped_data:
                    grouped_data[setting.country] = []

                grouped_data[setting.country].append({
                    "currency": setting.currency,
                    "deposit_percent": setting.deposit_percent,
                    "withdraw_percent": setting.withdraw_percent,
                    "deals": [
                        {
                            "id": deal.id,
                            "amount": deal.amount,
                            "currency": deal.currency,
                            "method": deal.method,
                            "created_at": deal.created_at,
                            "status": deal.status,
                        }
                        for deal in deals
                    ],
                })

            data = [{"country": country, "details": details} for country, details in grouped_data.items()]
            serializer = self.serializer_class(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, 200)

        except Exception as e:
            return Response({"message": str(e)}, 400)
        

