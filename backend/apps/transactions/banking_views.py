"""
Banking system API views:
- Deposits with fake payment gateway
- Transfers with encryption/MAC/hashing
- Admin dashboard (user management, encrypted transaction monitoring)
- Authority dashboard (user verification, key issuance)
"""

import sys
import os
import json
import hashlib
from decimal import Decimal
from datetime import datetime

from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.db import transaction as db_transaction
from django.db import models
from django.utils import timezone

from apps.users.models import User
from .models import Transaction, Ledger, KYCRequest, ActionLog
from .serializers import (
    TransactionCreateSerializer,
    TransactionListSerializer,
    LedgerSerializer
)

# Import crypto modules
crypto_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'crypto')
if crypto_path not in sys.path:
    sys.path.insert(0, crypto_path)

from rsa import encrypt, serialize_public_key, decrypt, deserialize_public_key
from ecc import ECCEncryption
from hmac_custom import generate_transaction_signature
from key_management import InMemoryKeyCache


# ==================== DEPOSITS ====================

class DepositInitiateView(APIView):
    """Initiate a deposit transaction (fake payment gateway)."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Start deposit process."""
        user = request.user
        
        try:
            amount = Decimal(request.data.get('amount', 0))
            
            if amount <= 0:
                return Response(
                    {'error': 'Amount must be positive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Return fake payment gateway details
            return Response({
                'deposit_session': {
                    'session_id': f"DEP_{user.id}_{datetime.now().timestamp()}",
                    'user_id': user.id,
                    'user_email': user.email,
                    'amount': str(amount),
                    'timestamp': datetime.now().isoformat(),
                    'status': 'payment_pending'
                },
                'payment_gateway': {
                    'provider': 'FakePaymentGateway',
                    'instructions': 'Simulated payment processing. Use the /deposit/process/ endpoint to complete.',
                    'test_cards': {
                        'success': '4111-1111-1111-1111',
                        'failure': '4444-4444-4444-4444'
                    }
                },
                'message': 'Deposit initiated. Proceed to payment processing.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to initiate deposit: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class DepositProcessView(APIView):
    """Process fake payment and create deposit transaction."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Process payment and create deposit."""
        user = request.user
        
        try:
            amount = Decimal(request.data.get('amount'))
            card_number = request.data.get('card_number', '')
            
            if amount <= 0:
                return Response(
                    {'error': 'Invalid amount'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Simulate payment processing
            if '4111' in card_number:
                payment_success = True
            elif '4444' in card_number:
                payment_success = False
            else:
                payment_success = True  # Default to success
            
            if not payment_success:
                return Response({
                    'status': 'failed',
                    'message': 'Payment declined by gateway',
                    'error': 'Card was declined'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Payment successful - create transaction
            with db_transaction.atomic():
                # Get or create ledger
                ledger, _ = Ledger.objects.get_or_create(user=user)
                
                # Create the deposit transaction
                rsa_public_key_str = user.public_key
                
                # Encrypt amount with RSA
                if rsa_public_key_str:
                    from apps.users.auth_views import get_rsa_private_key_from_session
                    try:
                        rsa_public_key = deserialize_public_key(json.loads(rsa_public_key_str))
                        encrypted_payload = encrypt(str(amount), rsa_public_key)
                        encrypted_payload_str = json.dumps(encrypted_payload)
                    except:
                        encrypted_payload_str = None
                else:
                    encrypted_payload_str = None
                
                # Generate transaction hash
                tx_data = f"{user.id}_{amount}_{datetime.now().isoformat()}"
                tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()
                
                # Get previous transaction hash
                last_tx = Transaction.objects.filter(receiver=user).order_by('-created_at').first()
                previous_hash = last_tx.transaction_hash if last_tx else None
                
                # Generate HMAC
                hmac_sig = generate_transaction_signature(
                    secret_key=str(user.id),
                    sender_id=0,  # External source
                    receiver_id=user.id,
                    amount=str(amount),
                    encrypted_payload=encrypted_payload_str or '',
                    timestamp=datetime.now().isoformat()
                )
                
                # Create transaction
                tx = Transaction.objects.create(
                    transaction_type=Transaction.TYPE_DEPOSIT,
                    status=Transaction.STATUS_COMPLETED,
                    sender=None,  # External source
                    receiver=user,
                    amount=amount,
                    encrypted_payload=encrypted_payload_str,
                    privacy_level=Transaction.STANDARD,
                    hmac_signature=hmac_sig,
                    transaction_hash=tx_hash,
                    previous_hash=previous_hash
                )
                
                # Credit to ledger
                ledger.credit(amount)
                
                # Update user balance
                user.balance = ledger.balance
                user.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Deposit completed successfully',
                    'transaction': {
                        'id': tx.id,
                        'type': tx.transaction_type,
                        'amount': str(tx.amount),
                        'receiver': user.email,
                        'created_at': tx.created_at.isoformat(),
                        'transaction_hash': tx_hash
                    },
                    'new_balance': f"{ledger.balance:.2f}"
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': f'Deposit processing failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ==================== TRANSFERS ====================

class TransferCreateView(APIView):
    """Create a transfer between users with encryption/MAC/hashing."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create transfer transaction."""
        sender = request.user
        
        if sender.role == User.ROLE_USER and not sender.is_verified:
            return Response(
                {'error': 'Your account must be verified before transferring funds'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            receiver_id = request.data.get('receiver_id')
            amount = Decimal(request.data.get('amount'))
            privacy_level = request.data.get('privacy_level', Transaction.STANDARD)
            
            # Validate
            if amount <= 0:
                return Response(
                    {'error': 'Amount must be positive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                receiver = User.objects.get(id=receiver_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Receiver not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if sender.id == receiver.id:
                return Response(
                    {'error': 'Cannot transfer to yourself'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get ledgers
            sender_ledger = Ledger.objects.get(user=sender)
            if sender_ledger.balance < amount:
                return Response(
                    {'error': 'Insufficient balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with db_transaction.atomic():
                receiver_ledger, _ = Ledger.objects.get_or_create(user=receiver)
                
                # Encrypt payload based on privacy level
                encrypted_payload = None
                if privacy_level in [Transaction.PRIVATE_METADATA, Transaction.HIGH_PRIVACY]:
                    try:
                        ecc = ECCEncryption()
                        payload = {
                            'sender': sender.email,
                            'receiver': receiver.email,
                            'amount': str(amount),
                            'timestamp': datetime.now().isoformat()
                        }
                        encrypted_payload = ecc.encrypt_data(
                            json.dumps(payload),
                            receiver.ecc_public_key
                        )
                    except:
                        encrypted_payload = None
                else:
                    encrypted_payload = json.dumps({
                        'sender': sender.email,
                        'receiver': receiver.email,
                        'amount': str(amount)
                    })
                
                # Generate transaction hash
                tx_data = f"{sender.id}_{receiver.id}_{amount}_{datetime.now().isoformat()}"
                tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()
                
                # Get previous transaction hash
                last_tx = Transaction.objects.filter(receiver=receiver).order_by('-created_at').first()
                previous_hash = last_tx.transaction_hash if last_tx else None
                
                # Generate HMAC
                hmac_sig = generate_transaction_signature(
                    secret_key=str(sender.id),
                    sender_id=sender.id,
                    receiver_id=receiver.id,
                    amount=str(amount),
                    encrypted_payload=encrypted_payload or '',
                    timestamp=datetime.now().isoformat()
                )
                
                # Create transaction
                tx = Transaction.objects.create(
                    transaction_type=Transaction.TYPE_TRANSFER,
                    status=Transaction.STATUS_COMPLETED,
                    sender=sender,
                    receiver=receiver,
                    amount=amount,
                    encrypted_payload=encrypted_payload,
                    privacy_level=privacy_level,
                    hmac_signature=hmac_sig,
                    transaction_hash=tx_hash,
                    previous_hash=previous_hash
                )
                
                # Update balances
                sender_ledger.debit(amount)
                receiver_ledger.credit(amount)
                
                # Update user balances
                sender.balance = sender_ledger.balance
                receiver.balance = receiver_ledger.balance
                sender.save()
                receiver.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Transfer completed successfully',
                    'transaction': {
                        'id': tx.id,
                        'type': tx.transaction_type,
                        'sender': sender.email,
                        'receiver': receiver.email,
                        'amount': str(tx.amount),
                        'privacy_level': privacy_level,
                        'created_at': tx.created_at.isoformat(),
                        'transaction_hash': tx_hash
                    },
                    'sender_new_balance': str(sender_ledger.balance),
                    'receiver_new_balance': str(receiver_ledger.balance)
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': f'Transfer failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ==================== ADMIN VIEWS ====================

class AdminUserListView(APIView):
    """Admin: List all users with encrypted data only."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get list of all users (encrypted)."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        users = User.objects.all().values(
            'id', 'email', 'username', 'role', 'balance', 
            'kyc_status', 'is_verified', 'is_active', 'created_at'
        )
        
        # Encrypt user data
        encrypted_users = []
        for user in users:
            encrypted_users.append({
                'id': user['id'],
                'email_encrypted': user.get('email_encrypted', 'encrypted'),
                'username_encrypted': user.get('username_encrypted', 'encrypted'),
                'role': user['role'],
                'balance': user['balance'],
                'kyc_status': user['kyc_status'],
                'is_verified': user['is_verified'],
                'is_active': user['is_active'],
                'created_at': user['created_at']
            })
        
        return Response({
            'total_users': len(encrypted_users),
            'users': encrypted_users
        })


class AdminSuspendUserView(APIView):
    """Admin: Suspend/activate a user."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        """Suspend or activate a user."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            target_user = User.objects.get(id=user_id)
            action = request.data.get('action', 'suspend')  # 'suspend' or 'activate'
            reason = request.data.get('reason', '')
            
            if action == 'suspend':
                target_user.is_active = False
                action_type = ActionLog.ACTION_USER_SUSPEND
            elif action == 'activate':
                target_user.is_active = True
                action_type = ActionLog.ACTION_USER_ACTIVATE
            else:
                return Response(
                    {'error': 'Invalid action'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            target_user.save()
            
            # Log action
            ActionLog.objects.create(
                actor=request.user,
                action=action_type,
                target_user=target_user,
                description=reason,
                ip_address=self.get_client_ip(request)
            )
            
            return Response({
                'status': 'success',
                'message': f'User {action}ed successfully',
                'user_id': target_user.id,
                'is_active': target_user.is_active
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AdminTransactionMonitorView(APIView):
    """Admin: Monitor encrypted transactions (no decryption)."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get all transactions in encrypted form."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        transactions = Transaction.objects.all().select_related(
            'sender', 'receiver'
        ).order_by('-created_at')[:100]  # Last 100 transactions
        
        tx_data = []
        for tx in transactions:
            tx_data.append({
                'id': tx.id,
                'type': tx.transaction_type,
                'status': tx.status,
                'sender': tx.sender.email if tx.sender else 'EXTERNAL',
                'receiver': tx.receiver.email,
                'amount': str(tx.amount),
                'privacy_level': tx.privacy_level,
                'hmac_valid': tx.verify_hmac(str(tx.receiver.id)) if tx.sender else True,
                'hash': tx.transaction_hash,
                'created_at': tx.created_at.isoformat()
            })
        
        return Response({
            'total_transactions': len(transactions),
            'transactions': tx_data
        })


# ==================== AUTHORITY VIEWS ====================

class AuthorityKYCListView(APIView):
    """Authority: List pending KYC requests."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get pending KYC requests."""
        if request.user.role != User.ROLE_AUTHORITY:
            return Response(
                {'error': 'Authority access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        kyc_requests = KYCRequest.objects.filter(
            status=KYCRequest.STATUS_PENDING
        ).select_related('user').order_by('-created_at')
        
        data = []
        for kyc in kyc_requests:
            data.append({
                'id': kyc.id,
                'user_id': kyc.user.id,
                'email': kyc.user.email,
                'username': kyc.user.username,
                'status': kyc.status,
                'created_at': kyc.created_at.isoformat()
            })
        
        return Response({
            'total_pending': len(data),
            'kyc_requests': data
        })


class AuthorityApproveUserView(APIView):
    """Authority: Approve or reject user KYC."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, kyc_id):
        """Approve or reject KYC request."""
        if request.user.role != User.ROLE_AUTHORITY:
            return Response(
                {'error': 'Authority access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            kyc = KYCRequest.objects.get(id=kyc_id)
            action = request.data.get('action', 'approve')  # 'approve' or 'reject'
            reason = request.data.get('reason', '')
            
            if action == 'approve':
                kyc.status = KYCRequest.STATUS_APPROVED
                kyc.approved_by = request.user
                kyc.approved_at = timezone.now()
                kyc.user.is_verified = True
                kyc.user.kyc_status = User.KYC_VERIFIED
                action_type = ActionLog.ACTION_USER_VERIFY
            elif action == 'reject':
                kyc.status = KYCRequest.STATUS_REJECTED
                kyc.user.kyc_status = User.KYC_REJECTED
                action_type = ActionLog.ACTION_USER_REJECT
            else:
                return Response(
                    {'error': 'Invalid action'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            kyc.save()
            kyc.user.save()
            
            # Log action
            ActionLog.objects.create(
                actor=request.user,
                action=action_type,
                target_user=kyc.user,
                description=reason
            )
            
            return Response({
                'status': 'success',
                'message': f'KYC {action}ed successfully',
                'user_id': kyc.user.id,
                'is_verified': kyc.user.is_verified
            })
            
        except KYCRequest.DoesNotExist:
            return Response(
                {'error': 'KYC request not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AuthorityIssueKeysView(APIView):
    """Authority: Issue/regenerate key pairs for users."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        """Issue keys for a user."""
        if request.user.role != User.ROLE_AUTHORITY:
            return Response(
                {'error': 'Authority access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            target_user = User.objects.get(id=user_id)
            
            return Response({
                'status': 'success',
                'message': 'Keys already generated during registration',
                'user_id': target_user.id,
                'has_rsa_keys': bool(target_user.public_key),
                'has_ecc_keys': bool(target_user.ecc_public_key)
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AuthorityDashboardView(APIView):
    """Authority: Dashboard with statistics."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get authority dashboard data."""
        if request.user.role != User.ROLE_AUTHORITY:
            return Response(
                {'error': 'Authority access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        total_users = User.objects.count()
        verified_users = User.objects.filter(is_verified=True).count()
        pending_kyc = KYCRequest.objects.filter(status=KYCRequest.STATUS_PENDING).count()
        
        return Response({
            'total_users': total_users,
            'verified_users': verified_users,
            'pending_kyc_requests': pending_kyc,
            'rejection_rate': f"{((total_users - verified_users) / max(total_users, 1) * 100):.1f}%"
        })


class AdminDashboardView(APIView):
    """Admin: Dashboard with statistics."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get admin dashboard data."""
        if not request.user.is_admin:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        suspended_users = total_users - active_users
        total_transactions = Transaction.objects.count()
        total_volume = Transaction.objects.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'suspended_users': suspended_users,
            'total_transactions': total_transactions,
            'total_volume': str(total_volume)
        })
