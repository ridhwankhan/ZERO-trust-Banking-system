from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.users.views import UserViewSet, FreezeAccountView
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
from apps.transactions.views import PostViewSet
from apps.users.notification_views import NotificationListView, NotificationMarkReadView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'posts', PostViewSet, basename='posts')


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Lightweight deploy/version probe used to confirm Render is on the latest build."""
    return Response({
        'status': 'ok',
        'service': 'fiducia-api',
        'build': 'webauthn-stable-v5',
    })


urlpatterns = [
    path('health/', health_check, name='api_health'),
    path('', include(router.urls)),
    path('users/profile/freeze/', FreezeAccountView.as_view(), name='freeze_account'),
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('auth/admin-login/', AdminLoginView.as_view(), name='auth_admin_login'),
    path('auth/authority-login/', AuthorityLoginView.as_view(), name='auth_authority_login'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('auth/profile/', UserProfileView.as_view(), name='auth_profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth_change_password'),

    # Notification endpoints
    path('notifications/', NotificationListView.as_view(), name='notifications_list'),
    path('notifications/read/', NotificationMarkReadView.as_view(), name='notifications_mark_all_read'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notifications_mark_read'),

    # Two-factor authentication endpoints
    path('auth/2fa/setup/', TwoFactorSetupView.as_view(), name='2fa_setup'),
    path('auth/2fa/verify/', TwoFactorVerifyView.as_view(), name='2fa_verify'),
    path('auth/2fa/backup/', TwoFactorBackupView.as_view(), name='2fa_backup'),
    path('auth/2fa/status/', TwoFactorStatusView.as_view(), name='2fa_status'),

    path('transactions/', include('apps.transactions.urls')),
    path('audit/', include('apps.audit.urls')),
    path('security/', include('apps.security.urls')),
]
