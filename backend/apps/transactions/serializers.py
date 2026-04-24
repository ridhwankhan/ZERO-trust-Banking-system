import json
import sys
import os
from decimal import Decimal
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.conf import settings

from apps.users.models import User
from .models import Transaction, Ledger, TransactionMetadata

# Add crypto module to path
crypto_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'crypto')
if crypto_path not in sys.path:
    sys.path.insert(0, crypto_path)

from ecc import ECCEncryption, ecc_serialize_public_key, ecc_deserialize_public_key


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions with privacy handling."""
    
    receiver_id = serializers.IntegerField(write_only=True)
    description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    notes = serializers.CharField(write_only=True, required=False, allow_blank=True)
    category = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Transaction
        fields = [
            'receiver_id', 'amount', 'privacy_level',
            'description', 'notes', 'category'
        ]
    
    def validate(self, attrs):
        """Validate transaction data."""
        # Check sender has sufficient balance
        sender = self.context['request'].user
        amount = attrs.get('amount', Decimal('0'))
        
        try:
            sender_ledger = Ledger.objects.get(user=sender)
            if sender_ledger.balance < amount:
                raise serializers.ValidationError({
                    'amount': f'Insufficient balance. Available: {sender_ledger.balance}'
                })
        except Ledger.DoesNotExist:
            raise serializers.ValidationError({
                'sender': 'Sender has no ledger account'
            })
        
        # Validate receiver exists
        receiver_id = attrs.get('receiver_id')
        try:
            User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'receiver_id': 'Receiver not found'
            })
        
        # Validate amount
        if amount <= 0:
            raise serializers.ValidationError({
                'amount': 'Amount must be positive'
            })
        
        # Validate sender != receiver
        if sender.id == receiver_id:
            raise serializers.ValidationError({
                'receiver_id': 'Cannot send to yourself'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create transaction with appropriate privacy handling."""
        sender = self.context['request'].user
        receiver_id = validated_data.pop('receiver_id')
        receiver = User.objects.get(id=receiver_id)
        
        # Extract metadata fields
        description = validated_data.pop('description', '')
        notes = validated_data.pop('notes', '')
        category = validated_data.pop('category', '')
        
        privacy_level = validated_data.get('privacy_level', Transaction.STANDARD)
        amount = validated_data.get('amount')
        
        # Get receiver's ECC public key for encryption
        receiver_ecc_public = None
        if receiver.ecc_public_key:
            try:
                ecc = ECCEncryption()
                receiver_ecc_public = ecc.deserialize_public_key(receiver.ecc_public_key)
            except Exception:
                pass
        
        # Prepare payload based on privacy level
        encrypted_payload = None
        metadata = None
        
        if privacy_level == Transaction.STANDARD:
            # No encryption - store plaintext in payload
            payload = {
                'description': description,
                'notes': notes,
                'category': category,
                'sender_email': sender.email,
                'receiver_email': receiver.email
            }
            encrypted_payload = json.dumps(payload)
        
        elif privacy_level == Transaction.PRIVATE_METADATA:
            # Encrypt sensitive metadata using ECC
            if receiver_ecc_public:
                ecc = ECCEncryption()
                sensitive_data = {
                    'description': description,
                    'notes': notes,
                    'category': category
                }
                encrypted_payload = ecc.encrypt(json.dumps(sensitive_data), receiver_ecc_public)
            else:
                # Fallback if no ECC key available
                encrypted_payload = json.dumps({
                    'error': 'ECC key not available',
                    'category_visible': category
                })
            
            # Store category in visible field
            metadata = {
                'category_visible': category
            }
        
        elif privacy_level == Transaction.HIGH_PRIVACY:
            # Encrypt entire payload except amount
            # Include amount in encrypted payload for integrity verification
            sensitive_data = {
                'description': description,
                'notes': notes,
                'category': category,
                'sender_email': sender.email,
                'receiver_email': receiver.email,
                'amount': str(amount)  # Include amount for verification
            }
            
            if receiver_ecc_public:
                ecc = ECCEncryption()
                encrypted_payload = ecc.encrypt(json.dumps(sensitive_data), receiver_ecc_public)
            else:
                encrypted_payload = json.dumps({
                    'error': 'ECC key not available for high privacy encryption'
                })
        
        # Create transaction
        transaction = Transaction.objects.create(
            sender=sender,
            receiver=receiver,
            amount=amount,
            privacy_level=privacy_level,
            encrypted_payload=encrypted_payload,
            hmac_signature='pending'  # Will be updated after creation
        )
        
        # Generate HMAC signature
        secret_key = settings.SECRET_KEY
        hmac_signature = transaction.generate_hmac(secret_key)
        transaction.hmac_signature = hmac_signature
        transaction.save()
        
        # Create metadata for PRIVATE_METADATA level
        if privacy_level == Transaction.PRIVATE_METADATA and metadata:
            TransactionMetadata.objects.create(
                transaction=transaction,
                category_visible=metadata.get('category_visible')
            )
        
        # Update ledgers (ALWAYS happens regardless of privacy level)
        sender_ledger, _ = Ledger.objects.get_or_create(user=sender, defaults={'balance': Decimal('0')})
        receiver_ledger, _ = Ledger.objects.get_or_create(user=receiver, defaults={'balance': Decimal('0')})
        
        sender_ledger.debit(amount)
        receiver_ledger.credit(amount)
        
        return transaction


class TransactionListSerializer(serializers.ModelSerializer):
    """Serializer for listing transactions with privacy-aware field exposure."""
    
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    receiver_email = serializers.CharField(source='receiver.email', read_only=True)
    decrypted_payload = serializers.SerializerMethodField()
    metadata_visible = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'sender_email', 'receiver_email', 'amount',
            'privacy_level', 'encrypted_payload', 'decrypted_payload',
            'metadata_visible', 'hmac_signature', 'created_at'
        ]
    
    def get_decrypted_payload(self, obj):
        """
        Attempt to decrypt payload if user has access.
        Only the receiver can decrypt ECC-encrypted payloads.
        """
        user = self.context['request'].user
        
        # Only receiver can decrypt
        if obj.receiver != user:
            return {'access': 'denied', 'reason': 'Only receiver can decrypt'}
        
        # STANDARD level - no decryption needed
        if obj.privacy_level == Transaction.STANDARD:
            try:
                return json.loads(obj.encrypted_payload)
            except json.JSONDecodeError:
                return {'error': 'Invalid payload format'}
        
        # PRIVATE_METADATA or HIGH_PRIVACY - requires ECC decryption
        # Get ECC private key from session
        from apps.users.auth_views import get_ecc_private_key_from_session
        ecc_private_key = get_ecc_private_key_from_session(user.id)
        
        if not ecc_private_key:
            return {
                'access': 'locked',
                'reason': 'Private key not in session. Please login again.'
            }
        
        try:
            ecc = ECCEncryption()
            decrypted = ecc.decrypt(obj.encrypted_payload, ecc_private_key)
            return json.loads(decrypted)
        except Exception as e:
            return {
                'access': 'error',
                'reason': f'Decryption failed: {str(e)}'
            }
    
    def get_metadata_visible(self, obj):
        """Get visible metadata for PRIVATE_METADATA transactions."""
        if obj.privacy_level == Transaction.PRIVATE_METADATA:
            try:
                metadata = obj.metadata
                return {
                    'category': metadata.category_visible
                }
            except TransactionMetadata.DoesNotExist:
                return {}
        return {}


class LedgerSerializer(serializers.ModelSerializer):
    """Serializer for ledger balance."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Ledger
        fields = ['user_email', 'balance', 'last_updated']
        read_only_fields = ['balance', 'last_updated']


class TransactionHistoryQuerySerializer(serializers.Serializer):
    """Serializer for query parameters in transaction history."""
    privacy_level = serializers.ChoiceField(
        choices=Transaction.PRIVACY_CHOICES,
        required=False
    )
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    min_amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False
    )
    max_amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False
    )
    as_sender = serializers.BooleanField(required=False, default=False)
    as_receiver = serializers.BooleanField(required=False, default=False)
