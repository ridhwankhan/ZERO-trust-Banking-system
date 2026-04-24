from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_USER = 'user'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_USER, 'User'),
        (ROLE_ADMIN, 'Admin'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)
    
    # RSA Key storage
    email_encrypted = models.TextField(null=True, blank=True, help_text="RSA encrypted email")
    username_encrypted = models.TextField(null=True, blank=True, help_text="RSA encrypted username")
    public_key = models.TextField(null=True, blank=True, help_text="RSA public key (e, n) in JSON")
    encrypted_private_key = models.TextField(null=True, blank=True, help_text="Password-encrypted RSA private key")
    
    # ECC Key storage
    ecc_public_key = models.TextField(null=True, blank=True, help_text="ECC public key (point) in JSON")
    ecc_encrypted_private_key = models.TextField(null=True, blank=True, help_text="Password-encrypted ECC private key")
    
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

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email
