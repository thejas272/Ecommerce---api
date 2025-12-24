from django.urls import path, include
from accounts import views


urlpatterns = [
    path('register/',views.RegisterAPIView.as_view(), name="register"),
    path('login/', views.LoginAPIView.as_view(), name="login"),
    path('refresh/',views.RefreshTokenAPIView.as_view(), name="refresh"),
    
]
