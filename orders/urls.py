from django.urls import path, include
from orders import views

urlpatterns = [
    path('checkout/',views.CheckoutPreviewAPIView.as_view(), name="checkout-preview"),

    path('',views.OrderAPIView.as_view(), name="order-create-list"),
    path('<str:id>/',views.OrderDetailAPIView.as_view(), name="order-detail"),
    path('<str:id>/cancel/',views.OrderCancelAPIView.as_view(), name="order-cancel"),
    path('item/<int:id>/cancel', views.OrderItemCancelAPIView.as_view(), name="order-item-cancel"),
]