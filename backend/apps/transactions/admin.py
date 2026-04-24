from django.contrib import admin
from .models import Transaction, Ledger, TransactionMetadata


@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['last_updated']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'receiver', 'amount', 'privacy_level', 'created_at']
    list_filter = ['privacy_level', 'created_at']
    search_fields = ['sender__email', 'receiver__email']
    readonly_fields = ['created_at', 'updated_at', 'hmac_signature']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('sender', 'receiver', 'amount', 'privacy_level')
        }),
        ('Privacy Data', {
            'fields': ('encrypted_payload', 'hmac_signature'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TransactionMetadata)
class TransactionMetadataAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'category_visible']
    search_fields = ['transaction__id', 'category_visible']
