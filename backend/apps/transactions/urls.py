from django.urls import path
from .views import (
    CreateTransactionView,
    TransactionHistoryView,
    LedgerBalanceView,
    TransactionDetailView,
    VerifyTransactionView,
    TransactionPrivacyStatsView
)
from .admin_views import (
    AdminTransactionListView,
    AdminUserTransactionView,
    AdminLedgerView,
    AdminVerifyTransactionView
)

urlpatterns = [
    # User transaction endpoints
    path('create/', CreateTransactionView.as_view(), name='transaction-create'),
    path('history/', TransactionHistoryView.as_view(), name='transaction-history'),
    path('<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('<int:pk>/verify/', VerifyTransactionView.as_view(), name='transaction-verify'),
    path('balance/', LedgerBalanceView.as_view(), name='ledger-balance'),
    path('privacy-stats/', TransactionPrivacyStatsView.as_view(), name='transaction-privacy-stats'),
    
    # Admin endpoints (RBAC protected)
    path('admin/all/', AdminTransactionListView.as_view(), name='admin-transaction-list'),
    path('admin/user/<int:user_id>/', AdminUserTransactionView.as_view(), name='admin-user-transactions'),
    path('admin/ledger/<int:user_id>/', AdminLedgerView.as_view(), name='admin-ledger-view'),
    path('admin/verify/<int:transaction_id>/', AdminVerifyTransactionView.as_view(), name='admin-verify-transaction'),
]
