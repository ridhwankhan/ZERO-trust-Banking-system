import sys
import os
from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User

# Add crypto module to path (crypto is at backend/crypto, we're in backend/apps/transactions)
crypto_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'crypto')
if crypto_path not in sys.path:
    sys.path.insert(0, crypto_path)

from hmac_custom import (
    generate_transaction_signature,
    verify_transaction_signature,
    HMACUtils
)


class Ledger(models.Model):
    """User account ledger for tracking balances."""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='ledger'
    )
    balance = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        default=0.00
    )
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ledgers'
        verbose_name = 'Ledger'
        verbose_name_plural = 'Ledgers'
    
    def __str__(self):
        return f"Ledger for {self.user.email} - Balance: {self.balance}"
    
    def credit(self, amount):
        """Add amount to balance."""
        if amount <= 0:
            raise ValidationError("Credit amount must be positive")
        self.balance += amount
        self.save()
    
    def debit(self, amount):
        """Subtract amount from balance."""
        if amount <= 0:
            raise ValidationError("Debit amount must be positive")
        if self.balance < amount:
            raise ValidationError("Insufficient balance")
        self.balance -= amount
        self.save()


class Transaction(models.Model):
    """
    Transaction model with 3 privacy levels and tamper-proof hashing.
    Supports both transfers and deposits.
    """
    
    # Transaction types
    TYPE_TRANSFER = 'transfer'
    TYPE_DEPOSIT = 'deposit'
    TYPE_WITHDRAWAL = 'withdrawal'
    TYPE_CHOICES = [
        (TYPE_TRANSFER, 'Transfer'),
        (TYPE_DEPOSIT, 'Deposit'),
        (TYPE_WITHDRAWAL, 'Withdrawal'),
    ]
    
    # Transaction status
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    # Privacy levels
    STANDARD = 'standard'
    PRIVATE_METADATA = 'private_metadata'
    HIGH_PRIVACY = 'high_privacy'
    
    PRIVACY_CHOICES = [
        (STANDARD, 'Standard'),
        (PRIVATE_METADATA, 'Private Metadata'),
        (HIGH_PRIVACY, 'High Privacy'),
    ]
    
    id = models.AutoField(primary_key=True)
    
    # Transaction type and status
    transaction_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default=TYPE_TRANSFER)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    # Participants (sender can be NULL for deposits)
    sender = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='sent_transactions',
        null=True,
        blank=True,
        help_text="NULL for deposits (external source)"
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='received_transactions'
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Transaction amount (always visible)"
    )
    
    # Encrypted payload - content varies by privacy level
    encrypted_payload = models.TextField(
        null=True,
        blank=True,
        help_text="Encrypted transaction data based on privacy level"
    )
    
    # Privacy level indicator
    privacy_level = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default=STANDARD
    )
    
    # HMAC signature for integrity verification
    hmac_signature = models.CharField(
        max_length=128,
        help_text="HMAC signature for transaction integrity"
    )
    
    # Tamper-proof chain hashing
    transaction_hash = models.CharField(
        max_length=256,
        unique=True,
        null=True,
        blank=True,
        help_text="SHA-256 hash of transaction data"
    )
    previous_hash = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text="Hash of previous transaction for chain integrity"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        sender_email = self.sender.email if self.sender else "EXTERNAL"
        return f"TX-{self.id}: {sender_email} -> {self.receiver.email} | {self.amount} | {self.transaction_type}"
    
    def generate_hmac(self, secret_key: str) -> str:
        """Generate HMAC signature for transaction integrity using custom HMAC."""
        return generate_transaction_signature(
            secret_key=secret_key,
            sender_id=self.sender.id,
            receiver_id=self.receiver.id,
            amount=str(self.amount),
            encrypted_payload=self.encrypted_payload or '',
            timestamp=str(self.created_at)
        )
    
    def verify_hmac(self, secret_key: str) -> bool:
        """Verify HMAC signature using custom HMAC with constant-time comparison."""
        return verify_transaction_signature(
            stored_signature=self.hmac_signature,
            secret_key=secret_key,
            sender_id=self.sender.id,
            receiver_id=self.receiver.id,
            amount=str(self.amount),
            encrypted_payload=self.encrypted_payload or '',
            timestamp=str(self.created_at)
        )
    
    def verify_comprehensive_integrity(self, secret_key: str) -> dict:
        """
        Comprehensive integrity verification including HMAC and data consistency.
        
        Args:
            secret_key: Secret key for HMAC verification
            
        Returns:
            Dictionary with detailed integrity verification results
        """
        verification_result = {
            'hmac_valid': False,
            'data_consistent': True,
            'privacy_level_valid': True,
            'amount_valid': True,
            'participants_valid': True,
            'timestamp_valid': True,
            'overall_integrity': False
        }
        
        try:
            # Verify HMAC signature
            verification_result['hmac_valid'] = self.verify_hmac(secret_key)
            
            # Verify data consistency
            if self.encrypted_payload:
                try:
                    # Try to parse encrypted payload based on privacy level
                    if self.privacy_level == self.STANDARD:
                        import json
                        payload_data = json.loads(self.encrypted_payload)
                        verification_result['data_consistent'] = True
                    else:
                        # For encrypted payloads, just verify it's not empty
                        verification_result['data_consistent'] = len(self.encrypted_payload) > 0
                except:
                    verification_result['data_consistent'] = False
            
            # Validate privacy level
            verification_result['privacy_level_valid'] = self.privacy_level in [
                self.STANDARD, self.PRIVATE_METADATA, self.HIGH_PRIVACY
            ]
            
            # Validate amount
            verification_result['amount_valid'] = self.amount > 0
            
            # Validate participants
            verification_result['participants_valid'] = (
                self.sender is not None and 
                self.receiver is not None and 
                self.sender.id != self.receiver.id
            )
            
            # Validate timestamp
            verification_result['timestamp_valid'] = self.created_at is not None
            
            # Overall integrity
            verification_result['overall_integrity'] = all([
                verification_result['hmac_valid'],
                verification_result['data_consistent'],
                verification_result['privacy_level_valid'],
                verification_result['amount_valid'],
                verification_result['participants_valid'],
                verification_result['timestamp_valid']
            ])
            
        except Exception as e:
            verification_result['error'] = str(e)
            verification_result['overall_integrity'] = False
        
        return verification_result
    
    def clean(self):
        """Validate transaction data."""
        if self.sender == self.receiver:
            raise ValidationError("Sender and receiver cannot be the same")
        if self.amount <= 0:
            raise ValidationError("Amount must be positive")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class TransactionMetadata(models.Model):
    """
    Additional metadata for transactions with PRIVATE_METADATA privacy level.
    Stores encrypted sensitive fields separately.
    """
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='metadata'
    )
    # Encrypted fields
    description_encrypted = models.TextField(null=True, blank=True)
    notes_encrypted = models.TextField(null=True, blank=True)
    category_encrypted = models.TextField(null=True, blank=True)
    
    # Non-sensitive fields (always visible)
    category_visible = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'transaction_metadata'
        verbose_name = 'Transaction Metadata'
        verbose_name_plural = 'Transaction Metadata'


class KYCRequest(models.Model):
    """KYC (Know Your Customer) verification management."""
    
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc_request')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    # Documentation (encrypted storage placeholder)
    document_hash = models.CharField(max_length=256, null=True, blank=True)
    verification_notes = models.TextField(null=True, blank=True)
    
    # Authority approval
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='kyc_approvals'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kyc_requests'
        verbose_name = 'KYC Request'
        verbose_name_plural = 'KYC Requests'
    
    def __str__(self):
        return f"KYC for {self.user.email} - {self.status}"


class ActionLog(models.Model):
    """Audit logging for admin and authority actions."""
    
    ACTION_USER_SUSPEND = 'user_suspend'
    ACTION_USER_ACTIVATE = 'user_activate'
    ACTION_USER_VERIFY = 'user_verify'
    ACTION_USER_REJECT = 'user_reject'
    ACTION_TRANSACTION_VIEW = 'transaction_view'
    ACTION_BALANCE_MODIFY = 'balance_modify'
    ACTION_CHOICES = [
        (ACTION_USER_SUSPEND, 'User Suspended'),
        (ACTION_USER_ACTIVATE, 'User Activated'),
        (ACTION_USER_VERIFY, 'User Verified'),
        (ACTION_USER_REJECT, 'User Rejected'),
        (ACTION_TRANSACTION_VIEW, 'Transaction Viewed'),
        (ACTION_BALANCE_MODIFY, 'Balance Modified'),
    ]
    
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='audit_actions')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='audit_targets'
    )
    
    # Action details
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'action_logs'
        verbose_name = 'Action Log'
        verbose_name_plural = 'Action Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.actor.email} - {self.action} - {self.created_at}"


class Post(models.Model):
    """Encrypted social post authored by a user."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    title_encrypted = models.TextField(help_text="RSA encrypted post title")
    content_encrypted = models.TextField(help_text="RSA encrypted post content")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']

    def __str__(self):
        return f"Post #{self.id} by {self.author.email}"
