from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'is_active', 'is_staff', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'username']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Timestamps', {'fields': ('role', 'created_at', 'updated_at')}),
        ('RSA Encryption', {'fields': ('public_key', 'encrypted_private_key', 'email_encrypted', 'username_encrypted')}),
        ('ECC Encryption', {'fields': ('ecc_public_key', 'ecc_encrypted_private_key')}),
    )
    readonly_fields = [
        'created_at', 'updated_at', 
        'public_key', 'encrypted_private_key', 'email_encrypted', 'username_encrypted',
        'ecc_public_key', 'ecc_encrypted_private_key'
    ]
