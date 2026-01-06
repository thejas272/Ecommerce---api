from django.db import models
from django.conf import settings
from products import models as product_models
from phonenumber_field.modelfields import PhoneNumberField
import uuid

# Create your models here.

class OrderModel(models.Model):

    STATUS_CHOICES =[("PENDING","Pending"),
                     ("PAID","Paid"),
                     ("SHIPPED","Shipped"),
                     ("DELIVERED","Delivered",),
                     ("RETURNED","Returned"),
                     ("CANCELLED","Cancelled"),
                    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE, null=False, blank=False)

    name         = models.CharField(max_length=300, null=False, blank=False)
    phone        = PhoneNumberField(null=False, blank=False)
    address_line = models.TextField(null=False, blank=False)
    city         = models.CharField(max_length=100, null=False, blank=False)
    state        = models.CharField(max_length=100, null=False, blank=False)
    pincode      = models.CharField(max_length=6, null=False, blank=False)

    subtotal     = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    grand_total  = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)


    status       = models.CharField(max_length=50, choices=STATUS_CHOICES, default="PENDING", null=False, blank=False)
    order_id     = models.CharField(max_length=36, unique=True, editable=False, db_index=True, null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self,*args,**kwargs):
        if not self.order_id:
            self.order_id = str(uuid.uuid4())

        return super().save(*args,**kwargs)

    def __str__(self):
        return f"{self.order_id}"



    

class OrderItemModel(models.Model):
    order   = models.ForeignKey(OrderModel, related_name="items", on_delete=models.CASCADE, null=False, blank=False)
    product = models.ForeignKey(product_models.ProductModel, related_name="order_items", on_delete=models.PROTECT, null=False, blank=False)

    product_name  = models.CharField(max_length=200, null=False, blank=False)
    category_name = models.CharField(max_length=200, null=False, blank=False)
    brand_name    = models.CharField(max_length=200, null=False, blank=False)

    product_slug  = models.CharField(max_length=200, null=False, blank=False)
    category_slug = models.CharField(max_length=200, null=False, blank=False)
    brand_slug    = models.CharField(max_length=200, null=False, blank=False)  

    unit_price  = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    quantity    = models.PositiveIntegerField(null=False, blank=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.order.order_id} - {self.product_name}"
    

