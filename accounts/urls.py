from django.urls import path, include
from accounts import views


urlpatterns = [
    path('register/',views.RegisterAPIView.as_view(),      name="register"),
    path('login/', views.LoginAPIView.as_view(),           name="login"),
    path('logout/',views.LogoutAPIView.as_view(),          name="logout"),
    path('refresh/',views.RefreshTokenAPIView.as_view(),   name="refresh"),
    path('me/',views.ProfileApiView.as_view(),             name="profile"),
    path('me/update/',views.UpdateProfileAPIView.as_view(), name="update"),
    path('me/update/password/',views.UpdatePasswordAPIView.as_view(), name="update_password"),
    
]
