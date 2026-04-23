import sys
import os
from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User

# Add crypto module to path
crypto_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'crypto')
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
    Transaction model with 3 privacy levels:
    - STANDARD: No encryption, all data visible
    - PRIVATE_METADATA: Encrypt sensitive fields (notes, description) using ECC
    - HIGH_PRIVACY: Encrypt entire payload except amount
    """
    
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
    sender = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='sent_transactions'
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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"TX-{self.id}: {self.sender.email} -> {self.receiver.email} | {self.amount} | {self.privacy_level}"
    
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
