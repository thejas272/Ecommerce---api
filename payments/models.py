from django.db import models
from orders import models as orders_models
# Create your models here.


class PaymentModel(models.Model):
    
    PAYMENT_METHOD_CHOICES = [("COD","Cod"),
                              ("RAZORPAY","Razorpay"),
                             ]
    
    STATUS_CHOICES = [("PENDING","Pending"),
                      ("SUCCESS","Success"),
                      ("FAILED","Failed"),
                      ("REFUNDED","Refunded"),
                     ]
    
    order    = models.ForeignKey(orders_models.OrderModel, related_name="payments", on_delete=models.CASCADE, null=False, blank=False)
    method   = models.CharField(max_length=100, choices=PAYMENT_METHOD_CHOICES, null=False, blank=False, db_index=True)
    status   = models.CharField(max_length=100, choices=STATUS_CHOICES, default="PENDING", db_index=True)
    amount   = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    currency = models.CharField(max_length=50, default="INR", null=False, blank=False)

    provider_order_id   = models.CharField(max_length=255, null=True, blank=True)
    provider_signature  = models.CharField(max_length=255, null=True, blank=True)
    provider_payment_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.order.order_id} - {self.provider} - {self.status}"

