from django.urls import path, include
from products import views

urlpatterns = [
    path('categories/', views.CategoryListAPIView.as_view(), name="category-list"),
    path('brands/', views.BrandListAPIView.as_view(), name="Brand-list"),
    path('products/', views.ProductListAPIView.as_view(), name="product-list"),

    path('categories/{slug}', views.CategoryDetailAPIView.as_view(), name="category-detail"),
]