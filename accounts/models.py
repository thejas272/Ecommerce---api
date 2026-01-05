from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models import Q
from phonenumber_field.modelfields import PhoneNumberField
# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True, blank=False)




class AuditLog(models.Model):
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action    = models.CharField(max_length=200, null=False, blank=False)
    model     = models.CharField(max_length=150, null=True, blank=True)
    object_id = models.CharField(max_length=50, null=True, blank=True)
    message   = models.TextField(null=True, blank=True)
    changes   = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.action}"
    


class AddressModel(models.Model):
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False)
    name         = models.CharField(max_length=300, null=False, blank=False)
    phone        = PhoneNumberField(null=False, blank=False)
    address_line = models.TextField(null=False, blank=False)
    city         = models.CharField(max_length=100, null=False, blank=False)
    state        = models.CharField(max_length=100, null=False, blank=False)
    pincode      = models.CharField(max_length=6, null=False, blank=False)
    is_default   = models.BooleanField(default=False, null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.address_line}"
    
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user"],
                                               condition=Q(is_default=True),
                                               name="single_default_address_per_user"
                                               )
                      ]
        
    

    



