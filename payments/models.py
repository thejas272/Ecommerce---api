from django.db import models
from orders import models as orders_models
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
# Create your models here.


class PaymentModel(models.Model):
    
    PAYMENT_METHOD_CHOICES = [("COD","Cod"),
                              ("RAZORPAY","Razorpay"),
                             ]
    
    
    STATUS_CHOICES = [("PENDING","Pending"),
                      ("SUCCESS","Success"),
                      ("FAILED","Failed"),
                      ("CANCELLED","Cancelled")
                     ]
    

    REFUND_INFO_CHOICES = [("NONE","None"),
                           ("REQUESTED","Requested"),
                           ("REFUNDED","Refunded")
                          ]
    

    PAYMENT_CONFIRMATION_CHOICES = [("PENDING","Pending"),
                                    ("CONFIRMED","Confirmed")
                                   ]
    

    order    = models.ForeignKey(orders_models.OrderModel, related_name="payments", on_delete=models.PROTECT, null=False, blank=False)
    method   = models.CharField(max_length=100, choices=PAYMENT_METHOD_CHOICES, null=False, blank=False, db_index=True)
    status   = models.CharField(max_length=100, choices=STATUS_CHOICES, default="PENDING", db_index=True)
    amount   = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    currency = models.CharField(max_length=50, default="INR", null=False, blank=False)

    provider_order_id   = models.CharField(max_length=255, null=True, blank=True)
    provider_payment_id = models.CharField(max_length=255, null=True, blank=True)

    refund_info  = models.CharField(max_length=50, choices=REFUND_INFO_CHOICES, default="NONE", null=False, blank=False)

    payment_confirmation = models.CharField(max_length=100, choices=PAYMENT_CONFIRMATION_CHOICES, default="PENDING", null=False, blank=False)

    processing_started_at = models.DateTimeField(null=True)  # to prevent race conditions
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.order.order_id} - {self.provider} - {self.status}"
    

    @property
    def is_paid(self):
        return self.status == "SUCCESS"
    

    @property
    def is_unpaid(self):
        if self.status in ["PENDING","FAILED"]:
            return True
        return False
    

    @property
    def can_refund(self):
        if self.is_paid and not self.payment_refunds.exists():
            return True
        return False


    @property
    def is_processing(self):
        if self.status != "PENDING":
            return False
        if self.processing_started_at and self.processing_started_at >= timezone.now() - timedelta(minutes=5):
            return True
        return False


    @property
    def can_retry(self):
        if self.status == "FAILED":
            return True
        elif (self.status == "PENDING" and self.created_at < timezone.now() - timedelta(minutes=15)):
            return True
        return False
    

    @property
    def is_webhook_mutable(self):
        if self.status in ["PENDING"]:    
            return True
        return False







class RefundModel(models.Model):
    REFUND_STATUS_CHOICES = [("PENDING","Pending"),
                             ("SUCCESS","Success"),
                             ("FAILED","Failed")
                            ]
    
    order      = models.ForeignKey(orders_models.OrderModel, related_name="order_refunds", on_delete=models.PROTECT, null=False,blank=False)
    payment    = models.ForeignKey(PaymentModel, related_name="payment_refunds", on_delete=models.PROTECT, null=False,blank=False)

    amount    = models.DecimalField(max_digits=10, decimal_places=2, null=False,blank=False)
    currency  = models.CharField(max_length=50, default="INR", null=False,blank=False)  
    method    = models.CharField(max_length=50, choices=PaymentModel.PAYMENT_METHOD_CHOICES, null=False,blank=False)
    reason    =  models.TextField(null=False,blank=False)

    status    = models.CharField(max_length=50, choices=REFUND_STATUS_CHOICES, default="PENDING", null=False,blank=False)

    provider_refund_id = models.CharField(max_length=255, null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.order.order_id} - {self.status}"
    




class RefundItemModel(models.Model):
    refund = models.ForeignKey(RefundModel, on_delete=models.CASCADE, related_name="refund_items", null=False, blank=False)
    item   = models.ForeignKey(orders_models.OrderItemModel, on_delete=models.PROTECT, related_name="item_refunds", null=False, blank=False)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    status = models.CharField(max_length=50, choices=RefundModel.REFUND_STATUS_CHOICES, default="PENDING", null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return f"{self.item.name} - {self.status}"
    

    class Meta:
        constraints = [models.UniqueConstraint(fields = ["item"],
                                               name = "unique_refund_per_item"
                                              )
                      ]