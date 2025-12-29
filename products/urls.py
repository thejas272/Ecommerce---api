from django.urls import path, include
from products import views

urlpatterns = [
    path('categories/', views.CategoryListAPIView.as_view(), name="category-list"),
    path('brands/', views.BrandListAPIView.as_view(), name="Brand-list"),
    path('', views.ProductListAPIView.as_view(), name="product-list"),

    path('categories/<slug:slug>', views.CategoryDetailAPIView.as_view(), name="category-detail"),
    path('brands/<slug:slug>', views.BrandDetailAPIView.as_view(), name="brand-detail"),
    path('<slug:slug>', views.ProductDetailAPIView.as_view(), name="product-detail"),

    path('admin/categories/', views.AdminCategoryAPIView.as_view(), name="admin-category"),
    path('admin/brands/', views.AdminBrandAPIView.as_view(), name="admin-brand"),
    path('admin/products/', views.AdminProductAPIView.as_view(), name="admin-product"),

    path('admin/categories/<int:id>', views.AdminCategoryDetailAPIView.as_view(), name="admin-category-detail"),
    path('admin/brands/<int:id>', views.AdminBrandDetailAPIView.as_view(), name="admin-brand-detail"),
    path('admin/products/<int:id>', views.AdminProductDetailAPIView.as_view(), name="admin-product-detail"),

]