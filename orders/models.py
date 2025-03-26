from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class OrderStatus(models.TextChoices):
    PENDING = "pending", _("Ожидание")
    CONFIRMED = "confirmed", _("Подтвержден")
    CANCELED = "canceled", _("Отменен")

class Order(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    operation = models.CharField(max_length=255)
    declared_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    debit_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    details = models.JSONField()
    listing_id = models.IntegerField()
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.id} - {self.status}"
    