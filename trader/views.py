from django.contrib.auth.models import update_last_login

from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from utils import BaseCRUD, CustomPagination
from .models import (
    Trader, PercentSettings, TraderPhone, CredsTrader
)
from .serializer import (
    RegisterTraderSeialzier,
    TraderPhoneSerialzier, TraderPhoneCreateSerializer,
    TraderCreadsSerializer, TraderCreadsCreateSerializer,
    UserTraderSerialzier, NotificationUrlTelegramTraderSerialzier,
    NotificationDataTelegramTraderSerialzier
)
from merchant.models import Deal
from merchant.serializer import DealSerialzier
from accounts.models import UserAccounts
from .tasks import update_balance_trader_and_merchant
from merchant.tasks import send_telegram_message_system, send_notification_to_webhook

from config import settings

class UserBaseViewSet(BaseCRUD):
    permission_classes = [AllowAny]
    serializer_class = UserTraderSerialzier
    pagination_class = CustomPagination

    _model = UserAccounts
    _serializer = serializer_class

    @swagger_auto_schema(
        request_body=RegisterTraderSeialzier,
        responses={200: UserTraderSerialzier, 400: 'Bad Request'},
        operation_summary="Create New Trader User Account",
        operation_description="This endpoint created new trader user account.",
        tags=["TRADER"]
    )
    def create(self, request):
        serializer = RegisterTraderSeialzier(data=request.data)
        if serializer.is_valid():
            user = UserAccounts.objects.create_user(
                login=serializer.data['email'],
                password=serializer.data['password']
            )
            user.is_active = True
            user.is_confirmed = True
            user.in_consideration = True
            user.save()

            trader = Trader.objects.create(
                user_account=user,
                email=serializer.data['email'],
                ava_balance=serializer.data['available_deposit'],
                block_balance=serializer.data['blocked_deposit']
            )

            PercentSettings.objects.create(
                user_id=trader,
                deposit_percent=serializer.data['deposit_percent'],
                withdraw_percent=serializer.data['withdraw_percent']
            )

            serialzier = self._serializer(trader)
            return Response(serialzier.data, 200)
        else:
            return Response(serializer.errors, 400)

    @swagger_auto_schema(
        responses={200: UserTraderSerialzier, 400: 'Bad Request'},
        operation_summary="Get info User Account",
        operation_description="This endpoint geting info user account.",
        tags=["TRADER"]
    )
    def me(self, request):
        try:
            user = UserAccounts.objects.get(id=request.user.id)
        except:
            return Response({"message": "This user not found system"}, 404)

        try:
            trader = Trader.objects.get(user_account=user)
        except:
            return Response({'message': "This user not found trader obj."}, 400)
        
        serialzier = self._serializer(trader)
        return Response(serialzier.data)
        

class TraderPhoneViewSet(BaseCRUD):
    permission_classes = [IsAuthenticated]
    serializer_class = TraderPhoneSerialzier
    pagination_class = CustomPagination

    _model = TraderPhone
    _serializer = serializer_class
    _serializer_create = TraderPhoneCreateSerializer

    @swagger_auto_schema(
        request_body=TraderPhoneCreateSerializer,
        responses={200: TraderPhoneSerialzier, 400: 'Bad Request'},
        operation_summary="Create New Trader phone ",
        operation_description="This endpoint created new trader phone.",
        tags=["TRADER"]
    )
    def create(self, request):
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})

        serializer = self._serializer_create(data=request.data)
        if serializer.is_valid():
            trader_phone = TraderPhone.objects.create(
                user_id=trader,
                name=serializer.data['name']
            )
            serializer_ = self._serializer(trader_phone).data
            return Response(serializer_, 200)
        else:
            return Response(serializer.errors, 400)
    
    @swagger_auto_schema(
        responses={200: TraderPhoneSerialzier, 400: 'Bad Request'},
        operation_summary="List Trader phone ",
        operation_description="This endpoint list trader phone.",
        tags=["TRADER"]
    )
    def lists(self, request):
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})
        
        trader_phones = TraderPhone.objects.filter(user_id=trader)
        serialzier = self._serializer(trader_phones, many=True).data
        return Response(serialzier, 200)

    @swagger_auto_schema(
        responses={200: '{"message": "OK"}', 400: 'Bad Request'},
        operation_summary="Delete Trader phone ",
        operation_description="This endpoint delete trader phone.",
        tags=["TRADER"]
    )
    def delete(self, request, phone_id: str):
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})
    
        try:
            phone_trader = TraderPhone.objects.get(id=phone_id)
        except:
            return Response({"message": 'This user not found phone'}, 400)
        phone_trader.delete()
        return Response({"message": 'OK'}, 200)


class TraderCreadsViewSet(BaseCRUD):
    permission_classes = [IsAuthenticated]
    serializer_class = TraderCreadsSerializer
    pagination_class = CustomPagination

    _model = CredsTrader
    _serializer = serializer_class
    _serializer_create = TraderCreadsCreateSerializer

    @swagger_auto_schema(
        request_body=TraderCreadsCreateSerializer,
        responses={200: TraderCreadsSerializer, 400: 'Bad Request'},
        operation_summary="Create New creads Trader ",
        operation_description="This endpoint created new creads trader.",
        tags=["TRADER"]
    )
    def create(self, request):
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})

        serialzier = self._serializer_create(data=request.data)
        if serialzier.is_valid():
            try:
                trade_phone = TraderPhone.objects.get(id=serialzier.data['phone_id'])
            except:
                return Response({'message': 'This phone_id not found'}, 400)
            
            trader_creads = CredsTrader.objects.create(
                phone_id=trade_phone,
                user_id=trader,
                card_number=serialzier.data['card_number'],
                method=serialzier.data['method'],
                max_op=serialzier.data['max_op'],
                holder=serialzier.data['holder'],
                status=serialzier.data['status'],
                bank=serialzier.data['bank'],
                country=serialzier.data['country'],
                currency=serialzier.data['currency']
            )

            serialzier_ = self._serializer(trader_creads).data
            return Response(serialzier_, 200)
        else:
            return Response(serialzier.errors, 400)
    
    @swagger_auto_schema(
        responses={200: TraderCreadsSerializer, 400: 'Bad Request'},
        operation_summary="List creads Trader phone ",
        operation_description="This endpoint list creads trader.",
        tags=["TRADER"]
    )
    def lists(self, request):
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})
        
        trader_creads = CredsTrader.objects.filter(user_id=trader)
        serialzier = self._serializer(trader_creads, many=True).data
        return Response(serialzier, 200)


    @swagger_auto_schema(
        responses={200: '{message: ok}' , 400: 'Bad Request'},
        operation_summary="Patch creads Trader toggle",
        operation_description="This endpoint patch creads trader toggle.",
        tags=["TRADER"]
    )
    def toggle(self, request, cred_id: str):
        try:
            trader_cread = CredsTrader.objects.get(id=cred_id)
        except:
            return Response({"message": 'This cred id not found'}, 400)
        if trader_cread.status:
            trader_cread.status = False
        else:
            trader_cread.status = True

        trader_cread.save()
        return Response({'message': 'ok'}, 200)
    

    @swagger_auto_schema(
        request_body=TraderCreadsCreateSerializer,
        responses={200: TraderCreadsSerializer, 400: 'Bad Request'},
        operation_summary="Update creads Trader phone ",
        operation_description="This endpoint update creads trader.",
        tags=["TRADER"]
    )
    def update(self, request, cred_id: str):
        try:
            trader_cread = CredsTrader.objects.get(id=cred_id)
        except:
            return Response({"message": 'This cred id not found'}, 400)
        
        serializer = TraderCreadsCreateSerializer(data=request.data)
        if serializer.is_valid():
            
            try:
                trader_phone = TraderPhone.objects.get(id=serializer.data['phone_id'])
                serializer.validated_data['phone_id'] = trader_phone
            except:
                return Response({"message": "This phone id not found"})
            
            try:
                trader = Trader.objects.get(user_account=request.user)
                serializer.validated_data['user_id'] = trader
            except:
                return Response({"message": 'Your not trader user'}, 409)

            for field, value in serializer.validated_data.items():
                setattr(trader_cread, field, value)
            trader_cread.save()
            return Response({"message": "Cred updated successfully"}, status=200)
        else:
            return Response(serializer.errors, status=400)


# Заявки - ввод
class TraderRequestViewSet(BaseCRUD):
    permission_classes = [IsAuthenticated]
    serializer_class = DealSerialzier
    pagination_class = CustomPagination

    _model = Deal
    _serializer = serializer_class  

    @swagger_auto_schema(
        responses={200: DealSerialzier, 400: 'Bad Request'},
        operation_summary="List deals request Trader",
        operation_description="This endpoint List deals request Trader.",
        tags=["TRADER"]
    )
    def trader_request_list(self, request):
        """Метод для плолучения заявок на ввод"""
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})
        
        deals = Deal.objects.filter(responsible_id=trader, type=Deal.DealType.DEPOSIT).order_by('-created_at')
        page = self.paginate_queryset(self.filter_queryset(deals))
        serializer = self._serializer(page, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data, 200)
    
    @swagger_auto_schema(
        responses={200: "{'message': 'OK'}", 400: 'Bad Request'},
        operation_summary="Toggle deal request status",
        operation_description="This endpoint Toggle deal request status.",
        tags=["TRADER"]
    )
    def toggle_trader_request(self, request, order_id: str):
        """Метод для обновления статуса у заявки трейдером"""
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})
        
        try:
            deal = Deal.objects.get(order_id=order_id, responsible_id=trader)
        except:
            return Response({"message": 'This order_id not found'}, 400)

        if deal.status == Deal.DealStatus.PENDING:
            deal.status = Deal.DealStatus.COMPLETED
            update_balance_trader_and_merchant.delay(deal_id=deal.id)

            # Отправляем системное уведомление
            message = f"Сделка оплачена! Сумма: {deal.amount} {deal.currency}. Реквезит: {deal.creds_id.card_number}. Трейдер: {trader.login}. Мерч: {deal.source_id.title}"
            send_telegram_message_system.delay(message, topic_type='create')
        
        deal.save()
        return Response({"message": 'OK'}, 200)


# Ордера - вывод
class TraderOrderViewSet(BaseCRUD):
    permission_classes = [IsAuthenticated]
    serializer_class = DealSerialzier
    pagination_class = CustomPagination

    _model = Deal
    _serializer = serializer_class  
    
    @swagger_auto_schema(
        responses={200: DealSerialzier, 400: 'Bad Request'},
        operation_summary="List deals order Trader",
        operation_description="This endpoint List deals order Trader.",
        tags=["TRADER"]
    )
    def trader_order_list(self, request):
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})

        deals = Deal.objects.filter(responsible_id=None, type=Deal.DealType.WITHDRAW, status=Deal.DealStatus.PENDING)
        page = self.paginate_queryset(self.filter_queryset(deals))
        serializer = self._serializer(page, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data, 200)
    


    @swagger_auto_schema(
        responses={200: DealSerialzier, 400: 'Bad Request'},
        operation_summary="Take deal order Trader to work",
        operation_description="This endpoint take deal order Trader to work",
        tags=["TRADER"]
    )
    def take_order_to_work(self, request, order_id: str, creds_id: str):
        """Метод для взятия сделки в работу"""
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})
        
        try:
            creds = CredsTrader.objects.get(id=creds_id, user_id=trader)
        except:
            return Response({"message": 'This creds not found'}, 400)

        try:
            deal = Deal.objects.get(order_id=order_id)
        except:
            return Response({"message": 'This order id not found'})

        if deal.responsible_id is None:
            deal.responsible_id = trader
            deal.creds_id = creds
            deal.withdraw_deal_save()

            # TODO: отправить системное уведомление

            return Response({'message': 'OK'}, 200)
        
        return Response({"message": 'The order is already being processed by the traderder'}, 400)

    @swagger_auto_schema(
        responses={200: DealSerialzier, 400: 'Bad Request'},
        operation_summary="List deal order active Trader to work",
        operation_description="This endpoint List deal order active Trader to work",
        tags=["TRADER"]
    )
    def list_active_order_trader(self, request):
        """Метод для получения списка активных ордеров"""
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})
        
        deals = Deal.objects.filter(responsible_id=trader, type=Deal.DealType.WITHDRAW,
                                    status=Deal.DealStatus.PENDING)
        serialzier = DealSerialzier(deals, many=True)
        return Response(serialzier.data, 200)
    

    @swagger_auto_schema(
        responses={200: "{'message': 'OK'}", 400: 'Bad Request'},
        operation_summary="Toggle status deal order Trader to work",
        operation_description="This endpoint toggle status deal order Trader to work",
        tags=["TRADER"]
    )
    def toggle_active_order(self, request, order_id: str):
        """Метод для изменения статуса у заявки"""
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})
        
        try:
            deal = Deal.objects.get(order_id=order_id)
        except:
            return Response({"message": 'This order id not found'}, 400)
        
        if deal.status == Deal.DealStatus.PENDING:
            deal.status = Deal.DealStatus.COMPLETED
        deal.save()

        # TODO: 2. Отправить кб мерчу

        return Response({'message': 'OK'}, 200)


    def webhook_to_client_approved(self, request, order_id: str):
        """Метод для апрува вывода клиента"""
        try:
            deal = Deal.objects.get(order_id=order_id)
        except:
            return Response({"message": 'This order id not found deal'}, 400)
        
        # TODO: сделать математику с балансами после кб от мерча нам
        """
        merchant.balance -= deal.amount_by_currency_merchant
        trader.ava_balance += deal.amount_by_currency_trader
        """



class NotificationTraderTelegramViewSet(BaseCRUD):
    permission_classes = [AllowAny]
    serializer_class = NotificationUrlTelegramTraderSerialzier
    pagination_class = CustomPagination

    _model = Trader
    _serializer = serializer_class  

    @swagger_auto_schema(
        responses={200: NotificationUrlTelegramTraderSerialzier, 400: 'Bad Request'},
        operation_summary="Get tg bot link for notification to Trader",
        operation_description="This endpoint Get tg bot link for notification to Trader",
        tags=["TRADER"]
    )
    def get_tg_bot_url(self, request):
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not role trader'})
        
        name_bot = settings.TG_BOT_NAME
        return Response({"tg_bot_url":f"https://t.me/{name_bot}?start={trader.id}"}, 200)


    @swagger_auto_schema(
        request_body=NotificationDataTelegramTraderSerialzier,
        responses={200: "{'message': 'OK'}", 400: 'Bad Request'},
        operation_summary="Append telegram id by trader",
        operation_description="This endpoint Append telegram id by trader",
        tags=["TRADER"]
    )
    def append_telegram_id_to_trader(self, request):
        serialzier = self._serializer_create(data=request.data)
        if serialzier.is_valid():
            trader_id = serialzier.data['trader_id']
            telegram_id = serialzier.data['telegram_id']

            try:
                trader = Trader.objects.get(id=trader_id)
            except:
                return Response({"message": 'This user trader not found'}, 400)
            
            trader.telegram_id = telegram_id
            trader.save()
            return Response({'message': 'OK'}, 200)
        else:
            return Response(serialzier.errors, 400)
