from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('login/', views.UserLoginView.as_view(), name='user_login'),
    path('logout/', views.UserLogoutView.as_view(), name='user_logout'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('change-password/', views.PasswordChangeView.as_view(), name='change_password'),
    path('status/', views.user_status, name='user_status'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('vault/health/', views.vault_health_check, name='vault_health'),
    path('vault/rotate-keys/', views.rotate_encryption_keys, name='rotate_keys'),
]