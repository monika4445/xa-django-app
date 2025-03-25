from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Order, OrderStatus
from .serializers import OrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer
    
    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm_order(self, request, pk=None):
        """Confirm an order by changing its status."""
        order = get_object_or_404(Order, pk=pk)
        if order.status != OrderStatus.PENDING:
            return Response({"error": "Order cannot be confirmed."}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = OrderStatus.CONFIRMED
        order.save()
        return Response({"message": "Order confirmed successfully."}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["post"], url_path="appeal")
    def create_appeal(self, request, pk=None):
        """Create an appeal for an order."""
        order = get_object_or_404(Order, pk=pk)

        #TO - DO: Add logic to handle appeals. Appeals model is defined under the folder support in models.py file
        # Here, you would add logic to handle appeals (e.g., save an appeal record)
        return Response({"message": "Appeal created successfully."}, status=status.HTTP_201_CREATED)
