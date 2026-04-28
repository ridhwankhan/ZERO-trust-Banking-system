from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet
from apps.users.auth_views import (
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    UserProfileView,
    ChangePasswordView,
    AdminLoginView,
    AuthorityLoginView
)
from apps.users.two_factor_views import (
    TwoFactorSetupView,
    TwoFactorVerifyView,
    TwoFactorBackupView,
    TwoFactorStatusView
)

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('auth/admin-login/', AdminLoginView.as_view(), name='auth_admin_login'),
    path('auth/authority-login/', AuthorityLoginView.as_view(), name='auth_authority_login'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('auth/profile/', UserProfileView.as_view(), name='auth_profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth_change_password'),
    
    # Two-factor authentication endpoints
    path('auth/2fa/setup/', TwoFactorSetupView.as_view(), name='2fa_setup'),
    path('auth/2fa/verify/', TwoFactorVerifyView.as_view(), name='2fa_verify'),
    path('auth/2fa/backup/', TwoFactorBackupView.as_view(), name='2fa_backup'),
    path('auth/2fa/status/', TwoFactorStatusView.as_view(), name='2fa_status'),
    
    path('transactions/', include('apps.transactions.urls')),
    path('audit/', include('apps.audit.urls')),
]
