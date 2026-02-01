from django.db import models
from django.conf import settings
from accounts import models as accounts_models
from products import models as product_models
from phonenumber_field.modelfields import PhoneNumberField
import uuid

# Create your models here.

class OrderModel(models.Model):

    ORDER_STATUS_FLOW = {"PENDING"  : ["PAID","CONFIRMED","CANCELLED"],
                         "PAID"     : ["CONFIRMED","CANCELLED"],
                         "CONFIRMED": ["SHIPPED","CANCELLED"],
                         "SHIPPED"  : ["DELIVERED"],
                         "DELIVERED": ["RETURNED"],
                        }
    
    STATUS_CHOICES =[("CREATED","Created"),
                     ("CONFIRMED","Confirmed"),
                     ("SHIPPED","Shipped"),
                     ("DELIVERED","Delivered",),
                     ("CANCELLED","Cancelled"),
                    ]
    
    RETURN_INFO_CHOICES = [("NONE","None"),
                           ("REQUESTED","Requested"),
                           ("RETURNED","Returned"),
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


    status      = models.CharField(max_length=50, choices=STATUS_CHOICES, default="CREATED", null=False, blank=False)
    return_info = models.CharField(max_length=50, choices=RETURN_INFO_CHOICES, default="NONE", null=False, blank=False)
    order_id    = models.CharField(max_length=36, unique=True, editable=False, db_index=True, null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self,*args,**kwargs):
        if not self.order_id:
            self.order_id = str(uuid.uuid4())

        return super().save(*args,**kwargs)

    def __str__(self):
        return f"{self.order_id}"
    

    @property
    def is_all_items_payable(self):
        return all(item.is_payable for item in self.items.all())
    
    
    @property
    def is_all_items_cancellable(self):
        return all(item.is_cancellable for item in self.items.all())
    
    
    @property
    def is_cancelled(self):
        return all(item.status=="CANCELLED" for item in self.items.all())
    

    @property
    def is_all_items_returnable(self):
        return all(item.is_item_returnable for item in self.items.all())
    

    @property
    def was_return_requested(self):
        return all(item.was_item_return_requested for item in self.items.all())


    

class OrderItemModel(models.Model):

    ORDER_ITEM_STATUS_CHOICES = [("CREATED","Created"),
                                 ("CONFIRMED","Confirmed"),
                                 ("SHIPPED","Shipped"),
                                 ("DELIVERED","Delivered"),
                                 ("CANCELLED","Cancelled"),
                                ]
    
    RETURN_INFO_CHOICES = [("NONE","None"),
                           ("REQUESTED","Requested"),
                           ("RETURNED","Returned"),
                          ] 


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
    
    status      = models.CharField(max_length=50, choices=ORDER_ITEM_STATUS_CHOICES, null=False, blank=False, default="CREATED")
    return_info = models.CharField(max_length=50, choices=RETURN_INFO_CHOICES, null=False, blank=False, default="NONE")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.order.order_id} - {self.product_name}"
    
    @property
    def is_payable(self):
        if self.status in ["CREATED"] and self.return_info == "NONE":
            return True
        return False
    
    
    @property
    def is_cancellable(self):
        if self.status in ["CREATED","CONFIRMED"]:
            return True
        return False
    

    @property
    def is_item_returnable(self):
        if self.status == "DELIVERED" and self.return_info == "NONE":
            return True
        return False
    

    @property
    def was_item_return_requested(self):
        if self.status == "DELIVERED" and self.return_info == "REQUESTED":
            return True
        return False

    




class ReturnModel(models.Model):

    STATUS_CHOICES = [("CREATED","Created"),
                      ("CONFIRMED","Confirmed"),
                      ("PICKED_UP","Picked Up"),
                      ("RECEIVED","Received"),
                      ("REFUND_COMPLETED","Refund Completed")
                     ]


    requested_by = models.ForeignKey(accounts_models.User, related_name="returns", on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(OrderModel, related_name="order_returns", on_delete=models.CASCADE, null=False, blank=False)
    
    name         = models.CharField(max_length=300, null=False, blank=False)
    phone        = PhoneNumberField(null=False, blank=False)
    address_line = models.TextField(null=False, blank=False)
    city         = models.CharField(max_length=300, null=False, blank=False)
    state        = models.CharField(max_length=300, null=False, blank=False)
    pincode      = models.CharField(max_length=6, null=False, blank=False)
    reason       = models.CharField(max_length=300, null=False, blank=False)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="CREATED", null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order.order_id} - {self.status}"





class ReturnItemModel(models.Model):

    STATUS_CHOICES = [("CREATED","Created"),
                      ("CONFIRMED","Confirmed"),
                      ("PICKED_UP","Picked Up"),
                      ("RECEIVED","Received"),
                      ("REFUND_COMPLETED","Refund Completed")
                     ]


    return_instance = models.ForeignKey(ReturnModel, related_name="return_items", on_delete=models.CASCADE, null=False, blank=False)
    item  = models.ForeignKey(OrderItemModel, related_name="item_returns", on_delete=models.CASCADE, null=False, blank=False, db_index=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="CREATED", null=False, blank=False)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.return_instance} - {self.item} - {self.status}"
    

    class Meta:
        constraints = [models.UniqueConstraint(fields=["item"],
                                               name = "unique_return_per_item"
                                              )
                      ]