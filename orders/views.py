from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from .models import Order, OrderStatus
from .serializers import OrderSerializer
from django.utils.dateparse import parse_datetime
from support.models import Appeal

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer

    # Override default tags
    def get_view_name(self):
        return "Orders"

    def get_tags(self):
        return ["Orders"]

    @swagger_auto_schema(
        responses={200: "Order confirmed successfully.", 400: "Order cannot be confirmed."},
        operation_summary="Confirm Order",
        operation_description="This endpoint confirms an order by changing its status to CONFIRMED."
    )
    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm_order(self, request, pk=None):
        """Confirm an order by changing its status."""
        order = get_object_or_404(Order, pk=pk)
        if order.status != OrderStatus.PENDING:
            return Response({"error": "Order cannot be confirmed."}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = OrderStatus.CONFIRMED
        order.save()
        return Response({"message": "Order confirmed successfully."}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
    responses={201: "Запрос успешно создан."},
    operation_summary="Создание запроса по заказу",
    operation_description="Этот эндпоинт позволяет пользователям создать запрос по заказу."
)
    @action(detail=True, methods=["post"], url_path="appeal")
    def create_appeal(self, request, pk=None):
        """
        Создание запроса (апелляции) по заказу.
        """
        order = get_object_or_404(Order, pk=pk)
        
        # Извлекаем данные из запроса
        invoice_id = request.data.get('invoice_id')
        amount = request.data.get('amount')
        sup_id = request.data.get('sup_id')          # ID пользователя поддержки
        provider_id = request.data.get('provider_id')  # ID провайдера (опционально)
        responsible_id = request.data.get('responsible_id')  # ID трейдера (опционально)
        expiration_at = request.data.get('expiration_at')      # Дата истечения в формате ISO 8601 (опционально)
        source_id = request.data.get('source_id')      # ID мерчанта
        documents = request.data.get('documents', [])  # Список документов (опционально)
        
        # Проверяем, что обязательные поля присутствуют
        if not invoice_id or not amount or not sup_id or not source_id:
            return Response(
                {"error": "Необходимы поля invoice_id, amount, sup_id и source_id."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Преобразуем amount в число с плавающей запятой
        try:
            amount = float(amount)
        except ValueError:
            return Response({"error": "Неверный формат поля amount."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Преобразуем expiration_at в datetime, если передано
        if expiration_at:
            expiration_at = parse_datetime(expiration_at)
        
        # Создаем запись апелляции, связывая order_id с найденным заказом.
        # Используем суффикс _id для присвоения по идентификатору внешних ключей.
        appeal = Appeal.objects.create(
            order_id=str(order.id),  # Преобразуем идентификатор заказа в строку, так как order_id — CharField
            invoice_id=invoice_id,
            amount=amount,
            sup_id_id=sup_id,         # Передаем ID пользователя поддержки
            provider_id_id=provider_id,    # Передаем ID провайдера (если предоставлен)
            responsible_id_id=responsible_id,  # Передаем ID трейдера (если предоставлен)
            expiration_at=expiration_at,    # Передаем дату истечения (если предоставлена)
            source_id_id=source_id,    # Передаем ID мерчанта
            documents=documents
        )
        
        return Response(
            {"message": "Запрос успешно создан.", "appeal_id": str(appeal.id)},
            status=status.HTTP_201_CREATED
        )