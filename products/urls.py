from django.urls import path, include
from products import views

urlpatterns = [
    path('categories/', views.CategoryListAPIView.as_view(), name="category-list"),
    path('brands/', views.BrandListAPIView.as_view(), name="Brand-list"),
    path('', views.ProductListAPIView.as_view(), name="product-list"),

    path('categories/<slug:slug>', views.CategoryDetailAPIView.as_view(), name="category-detail"),
    path('brands/<slug:slug>', views.BrandDetailAPIView.as_view(), name="brand-detail"),
    path('<slug:slug>', views.ProductDetailAPIView.as_view(), name="product-detail"),

    path('admin/categories/', views.CategoryCreateAPIView.as_view(), name="category-create"),
    path('admin/brands/', views.BrandCreateAPIView.as_view(), name="brand-create"),
    path('admin/products/', views.ProductCreateAPIView.as_view(), name="product-create"),

    path('admin/categories/<int:id>', views.CategoryUpdateDeleteAPIView.as_view(), name="category-delete-update"),
    path('admin/brands/<int:id>', views.BrandDeleteUpdateAPIView.as_view(), name="brand-delete-update"),
    path('admin/products/<int:id>', views.ProductDeleteUpdateAPIView.as_view(), name="product-delete-update"),

]