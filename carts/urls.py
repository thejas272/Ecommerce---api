from django.urls import path, include
from carts import views



urlpatterns = [
    path('', views.AddToCartAPIView.as_view(), name="add-to-cart"),
    path('<int:id>/',views.CartItemAPIView.as_view(), name="update-cart-quantity"),
]