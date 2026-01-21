from django.urls import path, include
from orders import views

urlpatterns = [
    path('checkout/',views.CheckoutPreviewAPIView.as_view(), name="checkout-preview"),

    path('',views.OrderAPIView.as_view(), name="order-create-list"),
    path('<str:id>/',views.OrderDetailAPIView.as_view(), name="order-detail"),

    path('<str:id>/cancel/',views.OrderCancelAPIView.as_view(), name="order-cancel"),
    path('item/<int:id>/cancel', views.OrderItemCancelAPIView.as_view(), name="order-item-cancel"),
    
    path('<str:order_id>/return/', views.OrderReturnAPIView.as_view(), name="order-return"),
    path('item/<int:id>/return/', views.OrderItemReturnAPIView.as_view(), name="order-item-return"),
]