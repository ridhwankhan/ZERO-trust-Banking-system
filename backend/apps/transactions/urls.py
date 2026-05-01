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
from .banking_views import (
    # Deposits
    DepositInitiateView,
    DepositProcessView,
    # Transfers
    TransferCreateView,
    # Admin
    AdminUserListView,
    AdminSuspendUserView,
    AdminTransactionMonitorView,
    AdminDashboardView,
    # Authority
    AuthorityKYCListView,
    AuthorityApproveUserView,
    AuthorityIssueKeysView,
    AuthorityDashboardView,
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
    
    # ==================== BANKING SYSTEM URLs ====================
    
    # Deposit endpoints
    path('deposit/initiate/', DepositInitiateView.as_view(), name='deposit-initiate'),
    path('deposit/process/', DepositProcessView.as_view(), name='deposit-process'),
    
    # Transfer endpoints
    path('transfer/create/', TransferCreateView.as_view(), name='transfer-create'),
    
    # Admin dashboard endpoints
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-users-list'),
    path('admin/users/<int:user_id>/suspend/', AdminSuspendUserView.as_view(), name='admin-suspend-user'),
    path('admin/transactions/', AdminTransactionMonitorView.as_view(), name='admin-monitor-transactions'),
    
    # Authority dashboard endpoints
    path('authority/dashboard/', AuthorityDashboardView.as_view(), name='authority-dashboard'),
    path('authority/kyc/', AuthorityKYCListView.as_view(), name='authority-kyc-list'),
    path('authority/kyc/<int:kyc_id>/approve/', AuthorityApproveUserView.as_view(), name='authority-approve-kyc'),
    path('authority/keys/<int:user_id>/', AuthorityIssueKeysView.as_view(), name='authority-issue-keys'),
]
