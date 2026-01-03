from django.urls import path, include
from accounts import views


urlpatterns = [
    path('register/',views.RegisterAPIView.as_view(),      name="register"),
    path('login/', views.LoginAPIView.as_view(),           name="login"),
    path('logout/',views.LogoutAPIView.as_view(),          name="logout"),
    path('refresh/',views.RefreshTokenAPIView.as_view(),   name="refresh"),

    path('me/',views.ProfileApiView.as_view(),             name="me"),
    path('me/password/',views.UpdatePasswordAPIView.as_view(), name="change-password"),


    path('admin/users/',views.UserListAPIView.as_view(), name="user-list"),
    path('admin/audit-logs/',views.AuditLogListAPIView.as_view(), name="audit_log_list"),
    
    path('admin/users/<int:id>/',views.UserDetailAPIView.as_view(), name="admin-user-detail"),
    
]
