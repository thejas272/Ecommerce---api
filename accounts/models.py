from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

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
    



