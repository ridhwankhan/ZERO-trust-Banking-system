import sys
import os
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction as db_transaction
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from decimal import Decimal

from django.db import models
from .models import Transaction, Ledger, Post
from .serializers import (
    TransactionCreateSerializer,
    TransactionListSerializer,
    LedgerSerializer,
    TransactionHistoryQuerySerializer,
    PostSerializer,
)

# Add crypto module to path
crypto_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'crypto')
if crypto_path not in sys.path:
    sys.path.insert(0, crypto_path)

from rsa import encrypt as rsa_encrypt, deserialize_public_key


class CreateTransactionView(generics.CreateAPIView):
    """Create a new transaction with privacy handling."""
    serializer_class = TransactionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Create transaction with atomic ledger updates."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with db_transaction.atomic():
                transaction = serializer.save()
                
                response_data = {
                    'transaction': {
                        'id': transaction.id,
                        'sender': transaction.sender.email,
                        'receiver': transaction.receiver.email,
                        'amount': str(transaction.amount),
                        'privacy_level': transaction.privacy_level,
                        'created_at': transaction.created_at
                    },
                    'message': 'Transaction created successfully'
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': f'Transaction failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class TransactionHistoryView(generics.ListAPIView):
    """Get transaction history for authenticated user."""
    serializer_class = TransactionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter transactions based on query parameters."""
        user = self.request.user
        queryset = Transaction.objects.filter(
            Q(sender=user) | Q(receiver=user)
        )
        
        # Parse query parameters
        query_serializer = TransactionHistoryQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data
        
        # Filter by privacy level
        if params.get('privacy_level'):
            queryset = queryset.filter(privacy_level=params['privacy_level'])
        
        # Filter by date range
        if params.get('start_date'):
            queryset = queryset.filter(created_at__gte=params['start_date'])
        if params.get('end_date'):
            queryset = queryset.filter(created_at__lte=params['end_date'])
        
        # Filter by amount range
        if params.get('min_amount'):
            queryset = queryset.filter(amount__gte=params['min_amount'])
        if params.get('max_amount'):
            queryset = queryset.filter(amount__lte=params['max_amount'])
        
        # Filter by role (sender/receiver)
        if params.get('as_sender') and not params.get('as_receiver'):
            queryset = queryset.filter(sender=user)
        elif params.get('as_receiver') and not params.get('as_sender'):
            queryset = queryset.filter(receiver=user)
        
        return queryset.select_related('sender', 'receiver').prefetch_related('metadata')
    
    def list(self, request, *args, **kwargs):
        """Return paginated transaction history with summary."""
        queryset = self.get_queryset()
        
        # Get summary statistics
        total_sent = sum(
            t.amount for t in queryset.filter(sender=request.user)
        )
        total_received = sum(
            t.amount for t in queryset.filter(receiver=request.user)
        )
        
        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'summary': {
                    'total_transactions': queryset.count(),
                    'total_sent': str(total_sent),
                    'total_received': str(total_received),
                    'net_change': str(total_received - total_sent)
                },
                'transactions': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'summary': {
                'total_transactions': queryset.count(),
                'total_sent': str(total_sent),
                'total_received': str(total_received),
                'net_change': str(total_received - total_sent)
            },
            'transactions': serializer.data
        })


class LedgerBalanceView(APIView):
    """Get current ledger balance for authenticated user."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return user's ledger balance."""
        try:
            ledger = Ledger.objects.get(user=request.user)
            serializer = LedgerSerializer(ledger)
            return Response({
                'balance': f"{ledger.balance:.2f}",
                'last_updated': ledger.last_updated,
                'data': serializer.data
            })
        except Ledger.DoesNotExist:
            # Create ledger if doesn't exist
            ledger = Ledger.objects.create(user=request.user, balance=Decimal('0'))
            return Response({
                'balance': str(ledger.balance),
                'last_updated': ledger.last_updated,
                'message': 'New ledger created'
            })


class TransactionDetailView(generics.RetrieveAPIView):
    """Get detailed view of a specific transaction."""
    serializer_class = TransactionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """User can only view their own transactions."""
        user = self.request.user
        return Transaction.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'receiver').prefetch_related('metadata')
    
    def get_object(self):
        """Get transaction by ID with permission check."""
        pk = self.kwargs.get('pk')
        user = self.request.user
        
        try:
            transaction = Transaction.objects.get(
                Q(sender=user) | Q(receiver=user),
                id=pk
            )
            return transaction
        except Transaction.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Transaction not found or access denied')


class VerifyTransactionView(APIView):
    """Verify transaction integrity using HMAC."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk=None):
        """Verify a transaction's HMAC signature."""
        if not pk:
            return Response(
                {'error': 'Transaction ID required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        try:
            transaction = Transaction.objects.get(
                Q(sender=user) | Q(receiver=user),
                id=pk
            )
        except Transaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from django.conf import settings
        is_valid = transaction.verify_hmac(settings.SECRET_KEY)
        
        return Response({
            'transaction_id': transaction.id,
            'is_valid': is_valid,
            'privacy_level': transaction.privacy_level,
            'message': 'Transaction integrity verified' if is_valid else 'Transaction integrity check failed'
        })


class TransactionPrivacyStatsView(APIView):
    """Get statistics on transaction privacy levels for user."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return privacy level distribution for user's transactions."""
        user = request.user
        
        # Count by privacy level
        stats = {
            'sent': {
                Transaction.STANDARD: 0,
                Transaction.PRIVATE_METADATA: 0,
                Transaction.HIGH_PRIVACY: 0
            },
            'received': {
                Transaction.STANDARD: 0,
                Transaction.PRIVATE_METADATA: 0,
                Transaction.HIGH_PRIVACY: 0
            }
        }
        
        # Aggregate sent transactions
        for level, count in Transaction.objects.filter(
            sender=user
        ).values('privacy_level').annotate(
            count=models.Count('id')
        ).values_list('privacy_level', 'count'):
            stats['sent'][level] = count
        
        # Aggregate received transactions
        for level, count in Transaction.objects.filter(
            receiver=user
        ).values('privacy_level').annotate(
            count=models.Count('id')
        ).values_list('privacy_level', 'count'):
            stats['received'][level] = count
        
        return Response({
            'statistics': stats,
            'total_sent': sum(stats['sent'].values()),
            'total_received': sum(stats['received'].values())
        })


class PostViewSet(viewsets.ModelViewSet):
    """
    Encrypted posts feed.
    - Stores title/content encrypted with the author's RSA public key.
    - Returns decrypted fields when RSA private key is available in memory.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Post.objects.select_related('author').all()

    def _encrypt_post_data(self, user, title, content):
        if not user.public_key:
            raise ValueError("User public key missing. Re-login to regenerate keys.")
        public_key = deserialize_public_key(user.public_key)
        return (
            rsa_encrypt(title, public_key),
            rsa_encrypt(content, public_key),
        )

    def perform_create(self, serializer):
        title = self.request.data.get('title', '').strip()
        content = self.request.data.get('content', '').strip()
        if not title or not content:
            raise ValueError("Both title and content are required.")

        try:
            title_encrypted, content_encrypted = self._encrypt_post_data(
                self.request.user,
                title,
                content,
            )
        except Exception as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'error': str(exc)})

        serializer.save(
            author=self.request.user,
            title_encrypted=title_encrypted,
            content_encrypted=content_encrypted,
        )

    def perform_update(self, serializer):
        post = self.get_object()
        if post.author_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit your own posts.")

        title = self.request.data.get('title', '').strip()
        content = self.request.data.get('content', '').strip()
        if not title or not content:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'error': 'Both title and content are required.'})

        try:
            title_encrypted, content_encrypted = self._encrypt_post_data(
                self.request.user,
                title,
                content,
            )
        except Exception as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'error': str(exc)})

        serializer.save(
            title_encrypted=title_encrypted,
            content_encrypted=content_encrypted,
        )

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own posts.")
        instance.delete()
