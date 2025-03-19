from django.contrib.auth.models import update_last_login

from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser, FormParser

from utils import BaseCRUD, CustomPagination
from .models import (
    Appeal, SupportUser, Document
)
from .serializer import (
    RegisterSupportUserSerializer, SupportUserSerialzier,
    DocumentSerialzier, DocumentCreateSerialzier, 
    AppealCreateSerialzier, AppealSerializer,
    AppealAddDocumentSerialzier
)
from merchant.models import Deal, Merchant
from merchant.serializer import DealSerialzier
from accounts.models import UserAccounts
from trader.tasks import send_notification_to_merchant, update_balance_trader_and_merchant
from trader.models import Trader
from .tasks import schedule_check_appeal, schedule_notificatio_appeal_to_trader
from merchant.utils import return_balance_trader, update_balace_trader


class UserBaseViewSet(BaseCRUD):
    permission_classes = [AllowAny]
    serializer_class = SupportUserSerialzier
    pagination_class = CustomPagination

    _model = UserAccounts
    _serializer = serializer_class

    @swagger_auto_schema(
        request_body=RegisterSupportUserSerializer,
        responses={200: SupportUserSerialzier, 400: 'Bad Request'},
        operation_summary="Create New Support User Account",
        operation_description="This endpoint created new support user account.",
        tags=["SUPPORT"]
    )
    def create(self, request):
        serializer = RegisterSupportUserSerializer(data=request.data)
        if serializer.is_valid():
            user = UserAccounts.objects.create_user(
                login=serializer.data['email'],
                password=serializer.data['password']
            )
            user.is_active = True
            user.is_confirmed = True
            user.in_consideration = True
            user.save()

            support = SupportUser.objects.create(
                user_account=user,
                email=serializer.data['email']
            )

            serialzier = self._serializer(support)
            return Response(serialzier.data, 200)
        else:
            return Response(serializer.errors, 400)

    @swagger_auto_schema(
        responses={200: SupportUserSerialzier, 400: 'Bad Request'},
        operation_summary="Get info User Account",
        operation_description="This endpoint geting info user account.",
        tags=["SUPPORT"]
    )
    def me(self, request):
        try:
            user = UserAccounts.objects.get(id=request.user.id)
        except:
            return Response({"message": "This user not found system"}, 404)

        try:
            support = SupportUser.objects.get(user_account=user)
        except:
            return Response({'message': "This user not found support obj."}, 400)
        
        serialzier = self._serializer(support)
        return Response(serialzier.data)
        

class DocumentViewSet(BaseCRUD):
    permission_classes = [AllowAny]
    serializer_class = DocumentSerialzier
    pagination_class = CustomPagination
    parser_classes = (MultiPartParser, FormParser)

    _model = Document
    _serializer = serializer_class
    _serializer_create = DocumentCreateSerialzier

    @swagger_auto_schema(
        operation_summary="Upload document file",
        operation_description="Uploads a document file and returns its ID",
        tags=["DOCUMENT"],
        manual_parameters=[
            openapi.Parameter(
                name='file',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description='Файл документа для загрузки'
            )
        ],
        responses={200: DocumentSerialzier, 400: 'Bad Request'},
    )
    def create(self, request):
        serializer = self._serializer_create(data=request.data)
        if serializer.is_valid():
            document = serializer.save()
            serialzier_obj = self._serializer(document).data
            return Response(serialzier_obj, 200)
        else:
            return Response(serializer.errors, 400)


class AppealViewSet(BaseCRUD):
    permission_classes = [IsAuthenticated]
    serializer_class = AppealSerializer
    pagination_class = CustomPagination

    _model = Appeal
    _serializer = serializer_class
    _serializer_create = AppealCreateSerialzier

    @swagger_auto_schema(
        request_body=AppealCreateSerialzier,
        responses={200: AppealSerializer, 400: 'Bad Request'},
        operation_summary="Create New Appeal",
        operation_description="This endpoint create New Appeal",
        tags=["SUPPORT"]
    )
    def create(self, request):
        """Метод для создания апилки по сделке"""
        try:
            support = SupportUser.objects.get(user_account=request.user)
        except:
            return Response({'message': 'This user not have role support'}, 400)
        
        serialzier = self._serializer_create(data=request.data)
        if serialzier.is_valid():
            order_id = serialzier.data['order_id']
            amount = serialzier.data['amount']
            documents = serialzier.data['documents']

            try:
                deal = Deal.objects.get(order_id=order_id)
            except:
                try:
                    deal = Deal.objects.get(id=order_id)
                except:
                    return Response({'message': 'This order id not found deal'}, 400)
            
            if deal.status == Deal.DealStatus.PENDING or deal.status == Deal.DealStatus.DISPUTE:
                return Response({"message": "You can't open a dispute for a deal"}, 409)
            
            if deal.status == Deal.DealStatus.COMPLETED and float(deal.amount) == float(amount):
                # Вызываем функцию нотификации мерчанту 3 раза
                send_notification_to_merchant.delay(deal_id=deal.id)
                return Response({"message": 'OK'}, 200)
            
            merchant = Merchant.objects.get(id=deal.source_id.id)

            appeal = Appeal.objects.create(
                order_id=deal.order_id,
                invoice_id=deal.id,
                amount=amount,
                sup_id=support,
                responsible_id=deal.responsible_id,
                provider_id=deal.provider_id,
                source_id=deal.source_id,
                documents=[documents]
            )
            if float(merchant.max_amount_sla) > float(deal.amount_by_currency):
                schedule_check_appeal(appeal=appeal, deal=deal)

            schedule_notificatio_appeal_to_trader(deal)
            deal.status = Deal.DealStatus.DISPUTE
            deal.save()

            update_balace_trader(trader_id=deal.responsible_id.id, amount_by_currency_trader=float(deal.amount_by_currency_trader))

            serialzier_obj = self._serializer(appeal).data
            return Response(serialzier_obj, 200)
        else:
            return Response(serialzier.errors, 400)

    @swagger_auto_schema(
        responses={200: AppealSerializer, 400: 'Bad Request'},
        operation_summary="Lists Appeal",
        operation_description="This endpoint lists Appeal",
        tags=["SUPPORT"]
    )
    def list(self, request):
        """Метод для получения всех апилок у трейдера / саппорта"""
        try:
            support = SupportUser.objects.get(user_account=request.user)
            appeals = Appeal.objects.filter(sup_id=support)
        except:
            try:
                trader = Trader.objects.get(user_account=request.user)
                appeals = Appeal.objects.filter(responsible_id=trader)
            except:
                return Response({'message': "This user not found system"})
        
        serialzier = AppealSerializer(appeals, many=True)
        return Response(serialzier.data, 200)

    @swagger_auto_schema(
        request_body=AppealAddDocumentSerialzier,
        responses={200: AppealSerializer, 400: 'Bad Request'},
        operation_summary="Add trader file to Appeal",
        operation_description="This endpoint add trader file to Appeal",
        tags=["SUPPORT"]
    )
    def update_document_appeal_by_trader(self, request, appeal_id: str):
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': "This user not role trader"}, 400)
        
        try:
            appeal = Appeal.objects.get(id=appeal_id)
        except:
            return Response({"message": 'This appeal id not found'}, 400)
        
        serialzier = AppealAddDocumentSerialzier(data=request.data)
        if serialzier.is_valid():
            document_id = serialzier.data['document_id']

            if document_id in appeal.documents:
                return Response({'message': 'This document id a have in appeal'}, 400)
            
            appeal.documents.append(document_id)
            appeal.save()
            return Response({"message": "OK"}, 200)
        else:
            return Response(serialzier.errors, 400)
    
    @swagger_auto_schema(
        responses={200: AppealSerializer, 400: 'Bad Request'},
        operation_summary="Toogle appeal to trader",
        operation_description="This endpoint toogle appeal to trader",
        tags=["SUPPORT"]
    )
    def toggle_appeal_to_trader(self, request, appeal_id: str):
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': "This user not role trader"}, 400)
        
        try:
            appeal = Appeal.objects.get(id=appeal_id)
        except:
            return Response({"message": 'This appeal id not found'}, 400)
        
        deal = Deal.objects.get(order_id=appeal.order_id)
        appeal.status = Appeal.AppealStatus.CANCELED
        deal.status = Deal.DealStatus.CANCELED
        return_balance_trader(trader_id=trader.id, amount_by_currency_trader=deal.amount_by_currency_trader)
        appeal.save()

        return Response({'message': 'OK'}, 200)

    @swagger_auto_schema(
        responses={200: AppealSerializer, 400: 'Bad Request'},
        operation_summary="Toogle appeal to merchant",
        operation_description="This endpoint toogle appeal to merchant",
        tags=["SUPPORT"]
    )
    def toggle_appeal_to_merchant(self, request, appeal_id: str):
        try:
            trader = Trader.objects.get(user_account=request.user)
        except:
            return Response({'message': "This user not role trader"}, 400)
        
        try:
            appeal = Appeal.objects.get(id=appeal_id)
        except:
            return Response({"message": 'This appeal id not found'}, 400)

        deal = Deal.objects.get(order_id=appeal.order_id)
        appeal.status = Appeal.AppealStatus.CANCELED
        deal.status = Deal.DealStatus.COMPLETED
        update_balance_trader_and_merchant.delay(deal_id=deal.id)
        return Response({"message": 'OK'}, 200)

