from django.urls import path, include
from orders import views

urlpatterns = [
    path('checkout/',views.CheckoutPreviewAPIView.as_view(), name="checkout-preview"),
]