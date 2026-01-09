from django.urls import path, include
from carts import views



urlpatterns = [
    path('', views.CartListCreateAPIView.as_view(), name="list-add-to-cart"),
    path('<int:id>/',views.CartItemAPIView.as_view(), name="delete-cart-item"),
    path('<int:id>/quantity/',views.CartItemQuantityAPIView.as_view(), name="update-cart-quantity"),
]