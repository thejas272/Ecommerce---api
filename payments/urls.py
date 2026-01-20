from django.urls import path, include
from payments import views

urlpatterns = [
    path('initiate/',views.PaymentInitiateAPIView.as_view(), name="payment-initiate"),
    path('webhook/', views.PaymentWebhookAPIView.as_view(), name="payment-webhook"),

    path('retry/', views.PaymentRetryAPIView.as_view(), name="payment-retry"),
    path('status/<str:order_id>/',views.PaymentStatusAPIView.as_view(), name="payment-status"),
]