from django.urls import path, include
from payments import views

urlpatterns = [
    path('initiate/',views.PaymentInitiateAPIView.as_view(), name="payment-initiate"),
]