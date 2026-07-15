from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string


class User(AbstractUser):
    ROLE_USER = 'user'
    ROLE_ADMIN = 'admin'
    ROLE_AUTHORITY = 'authority'
    ROLE_CHOICES = [
        (ROLE_USER, 'User'),
        (ROLE_ADMIN, 'Admin'),
        (ROLE_AUTHORITY, 'Central Authority'),
    ]
    
    KYC_PENDING = 'pending'
    KYC_VERIFIED = 'verified'
    KYC_REJECTED = 'rejected'
    KYC_STATUS_CHOICES = [
        (KYC_PENDING, 'Pending Verification'),
        (KYC_VERIFIED, 'Verified'),
        (KYC_REJECTED, 'Rejected'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default=ROLE_USER)
    card_number = models.CharField(max_length=16, unique=True, null=True, blank=True, help_text="Virtual 16-digit card number")
    
    # Account balance for banking
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    
    # Account verification and KYC
    is_verified = models.BooleanField(default=False, help_text="User verified by Central Authority")
    kyc_status = models.CharField(max_length=10, choices=KYC_STATUS_CHOICES, default=KYC_PENDING)
    is_active = models.BooleanField(default=True, help_text="Account active status (Admin can suspend)")
    
    # RSA Key storage
    contact_info = models.TextField(null=True, blank=True, help_text="User contact info (phone/address)")
    contact_info_encrypted = models.TextField(null=True, blank=True, help_text="RSA encrypted contact info")
    email_encrypted = models.TextField(null=True, blank=True, help_text="RSA encrypted email")
    username_encrypted = models.TextField(null=True, blank=True, help_text="RSA encrypted username")
    public_key = models.TextField(null=True, blank=True, help_text="RSA public key (e, n) in JSON")
    encrypted_private_key = models.TextField(null=True, blank=True, help_text="Password-encrypted RSA private key")
    
    # ECC Key storage
    ecc_public_key = models.TextField(null=True, blank=True, help_text="ECC public key (point) in JSON")
    ecc_encrypted_private_key = models.TextField(null=True, blank=True, help_text="Password-encrypted ECC private key")
    
    # Two-step authentication
    two_factor_enabled = models.BooleanField(default=False, help_text="Enable two-factor authentication")
    two_factor_secret = models.CharField(max_length=32, null=True, blank=True, help_text="TOTP secret key")
    two_factor_backup_codes = models.TextField(null=True, blank=True, help_text="Backup codes for 2FA")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_user(self):
        return self.role == self.ROLE_USER
    
    @property
    def is_authority(self):
        return self.role == self.ROLE_AUTHORITY

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Auto-generate 16-digit card number if not present
        if not self.card_number:
            while True:
                new_card = ''.join(random.choices(string.digits, k=16))
                if not User.objects.filter(card_number=new_card).exists():
                    self.card_number = new_card
                    break
        super().save(*args, **kwargs)


class Notification(models.Model):
    """Stores in-app notifications for users, such as transfer receipts."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"
