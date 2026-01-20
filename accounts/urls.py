from django.urls import path, include
from accounts import views


urlpatterns = [
    path('register/',views.RegisterAPIView.as_view(),      name="register"),
    path('login/', views.LoginAPIView.as_view(),           name="login"),
    path('logout/',views.LogoutAPIView.as_view(),          name="logout"),
    path('refresh/',views.RefreshTokenAPIView.as_view(),   name="refresh"),


    path('me/',views.ProfileApiView.as_view(),             name="me"),
    path('me/password/',views.UpdatePasswordAPIView.as_view(), name="change-password"),


    path('address/', views.AddressApiView.as_view(), name="address-create-list"),
    path('address/<int:id>/',views.AddressDetailAPIView.as_view(), name="address-delete-update"),


    path('admin/users/',views.UserListAPIView.as_view(), name="admin-user-list"),
    path('admin/audit-logs/',views.AuditLogListAPIView.as_view(), name="admin-audit-log-list"),
    path('admin/orders/',views.AdminOrderListAPIView.as_view(), name="admin-order-list"),    

    path('admin/users/<int:id>/',views.UserDetailAPIView.as_view(), name="admin-user-detail"),
    path('admin/audit-logs/<int:id>/', views.AdminAuditLogDetailAPIView.as_view(), name="admin-audit-log-detail"),
    path('admin/orders/<str:id>/', views.AdminOrderDetailAPIView.as_view(), name="admin-order-detail"),

    path('admin/orders/<str:order_id>/payment', views.AdminOrderPaymentHistoryAPIView.as_view(), name="admin-order-payment-history"),
    
]
