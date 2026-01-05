from django.db import models

from accounts.models import User
from products.models import ProductModel
# Create your models here.



class CartModel(models.Model):
    user        = models.ForeignKey(User, related_name="cart_items", on_delete=models.CASCADE, null=False, blank=False)
    product     = models.ForeignKey(ProductModel, related_name="in_carts", on_delete=models.CASCADE, null=False, blank=False)
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    quantity    = models.PositiveIntegerField(default=1, null=False, blank=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    

    def save(self,*args,**kwargs):    
        self.total_price = self.unit_price * self.quantity

        return super().save(*args,**kwargs)
    

    class Meta:
        constraints = [
            models.UniqueConstraint(name="one_product_in_cart_per_user",
                                    fields=["user","product"]
                                    )
        ]
    