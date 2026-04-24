"""
Admin views for transactions with RBAC and audit logging.
Admins can view transactions but CANNOT decrypt HIGH_PRIVACY payloads.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from decimal import Decimal

from .models import Transaction, Ledger
from .serializers import TransactionListSerializer, LedgerSerializer
from .permissions import IsAdminUser
from apps.audit.models import AuditLog


class AdminTransactionListView(generics.ListAPIView):
    """
    Admin view to list all transactions.
    Admins can see transaction metadata but NOT decrypt HIGH_PRIVACY payloads.
    """
    serializer_class = TransactionListSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Return all transactions."""
        return Transaction.objects.all().select_related('sender', 'receiver')
    
    def list(self, request, *args, **kwargs):
        """List all transactions with audit logging."""
        # Log admin access
        AuditLog.log_admin_action(
            admin=request.user,
            action=AuditLog.ACTION_VIEW_ALL_TRANSACTIONS,
            details={'filter_params': dict(request.query_params)},
            request=request
        )
        
        queryset = self.get_queryset()
        
        # Get summary statistics
        total_count = queryset.count()
        total_amount = sum(t.amount for t in queryset)
        
        # Privacy level breakdown
        privacy_stats = {
            Transaction.STANDARD: queryset.filter(privacy_level=Transaction.STANDARD).count(),
            Transaction.PRIVATE_METADATA: queryset.filter(privacy_level=Transaction.PRIVATE_METADATA).count(),
            Transaction.HIGH_PRIVACY: queryset.filter(privacy_level=Transaction.HIGH_PRIVACY).count(),
        }
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            # Mask sensitive data for admin view
            data = self._prepare_admin_data(page)
            return self.get_paginated_response({
                'summary': {
                    'total_transactions': total_count,
                    'total_amount': str(total_amount),
                    'privacy_level_distribution': privacy_stats
                },
                'transactions': data
            })
        
        data = self._prepare_admin_data(queryset)
        return Response({
            'summary': {
                'total_transactions': total_count,
                'total_amount': str(total_amount),
                'privacy_level_distribution': privacy_stats
            },
            'transactions': data
        })
    
    def _prepare_admin_data(self, transactions):
        """
        Prepare transaction data for admin view.
        Admins CANNOT see decrypted payloads for HIGH_PRIVACY transactions.
        """
        data = []
        for tx in transactions:
            tx_data = {
                'id': tx.id,
                'sender': {
                    'id': tx.sender.id,
                    'email': tx.sender.email,
                    'username': tx.sender.username
                },
                'receiver': {
                    'id': tx.receiver.id,
                    'email': tx.receiver.email,
                    'username': tx.receiver.username
                },
                'amount': str(tx.amount),
                'privacy_level': tx.privacy_level,
                'hmac_signature': tx.hmac_signature,
                'created_at': tx.created_at,
                # Privacy notice for admin
                'admin_access_notice': self._get_privacy_notice(tx)
            }
            
            # For STANDARD level, show payload
            if tx.privacy_level == Transaction.STANDARD:
                tx_data['payload'] = tx.encrypted_payload
            # For PRIVATE_METADATA, show metadata (if exists) but not encrypted fields
            elif tx.privacy_level == Transaction.PRIVATE_METADATA:
                try:
                    tx_data['metadata'] = {
                        'category': tx.metadata.category_visible
                    }
                except Transaction.metadata.RelatedObjectDoesNotExist:
                    tx_data['metadata'] = {}
                tx_data['encrypted_fields'] = 'Encrypted - receiver only'
            # For HIGH_PRIVACY, DO NOT show any payload content
            elif tx.privacy_level == Transaction.HIGH_PRIVACY:
                tx_data['payload'] = '*** ENCRYPTED - ADMIN ACCESS DENIED ***'
            
            data.append(tx_data)
        
        return data
    
    def _get_privacy_notice(self, tx):
        """Get privacy notice based on transaction privacy level."""
        notices = {
            Transaction.STANDARD: 'Visible to admin',
            Transaction.PRIVATE_METADATA: 'Sensitive metadata encrypted - admin can see category only',
            Transaction.HIGH_PRIVACY: 'FULLY ENCRYPTED - admin cannot view payload'
        }
        return notices.get(tx.privacy_level, 'Unknown privacy level')


class AdminUserTransactionView(generics.ListAPIView):
    """
    Admin view to see a specific user's transactions.
    """
    serializer_class = TransactionListSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Return transactions for a specific user."""
        user_id = self.kwargs.get('user_id')
        return Transaction.objects.filter(
            Q(sender_id=user_id) | Q(receiver_id=user_id)
        ).select_related('sender', 'receiver')
    
    def list(self, request, *args, **kwargs):
        """List user transactions with audit logging."""
        from apps.users.models import User
        
        user_id = self.kwargs.get('user_id')
        target_user = None
        
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            pass
        
        # Log admin access
        AuditLog.log_admin_action(
            admin=request.user,
            action=AuditLog.ACTION_VIEW_USER_TRANSACTIONS,
            target_user=target_user,
            details={'target_user_id': user_id},
            request=request
        )
        
        queryset = self.get_queryset()
        
        # Use admin data preparation
        admin_view = AdminTransactionListView()
        data = admin_view._prepare_admin_data(queryset)
        
        return Response({
            'target_user_id': user_id,
            'target_user_email': target_user.email if target_user else None,
            'total_transactions': queryset.count(),
            'transactions': data
        })


class AdminLedgerView(APIView):
    """
    Admin view to see any user's ledger.
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request, user_id=None):
        """View user ledger with audit logging."""
        from apps.users.models import User
        
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create ledger
        ledger, created = Ledger.objects.get_or_create(
            user=target_user,
            defaults={'balance': Decimal('0')}
        )
        
        # Log admin access
        AuditLog.log_admin_action(
            admin=request.user,
            action=AuditLog.ACTION_VIEW_LEDGER,
            target_user=target_user,
            details={
                'ledger_created': created,
                'balance_viewed': str(ledger.balance)
            },
            request=request
        )
        
        return Response({
            'user': {
                'id': target_user.id,
                'email': target_user.email,
                'username': target_user.username
            },
            'ledger': {
                'balance': str(ledger.balance),
                'last_updated': ledger.last_updated,
                'is_new': created
            }
        })


class AdminVerifyTransactionView(APIView):
    """
    Admin view to verify any transaction's HMAC signature.
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, transaction_id=None):
        """Verify transaction HMAC with audit logging."""
        if not transaction_id:
            return Response(
                {'error': 'Transaction ID required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            transaction = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from django.conf import settings
        is_valid = transaction.verify_hmac(settings.SECRET_KEY)
        
        # Log admin access
        AuditLog.log_admin_action(
            admin=request.user,
            action=AuditLog.ACTION_VERIFY_TRANSACTION,
            target_transaction_id=transaction_id,
            details={
                'hmac_valid': is_valid,
                'privacy_level': transaction.privacy_level,
                'sender_id': transaction.sender_id,
                'receiver_id': transaction.receiver_id
            },
            request=request
        )
        
        # Prepare response with privacy restrictions
        response_data = {
            'transaction_id': transaction_id,
            'is_valid': is_valid,
            'privacy_level': transaction.privacy_level,
            'amount': str(transaction.amount),
            'sender_id': transaction.sender_id,
            'receiver_id': transaction.receiver_id,
            'created_at': transaction.created_at,
        }
        
        # Add payload info based on privacy level
        if transaction.privacy_level == Transaction.HIGH_PRIVACY:
            response_data['payload_access'] = 'DENIED - High privacy transaction'
        else:
            response_data['payload_access'] = 'Allowed'
        
        return Response(response_data)
