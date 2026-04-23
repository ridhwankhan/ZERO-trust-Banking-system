from django.db import models
from apps.users.models import User


class AuditLog(models.Model):
    """
    Audit log for tracking admin actions.
    Records when admins access sensitive data.
    """
    
    # Action types
    ACTION_VIEW_ALL_TRANSACTIONS = 'view_all_transactions'
    ACTION_VIEW_USER_TRANSACTIONS = 'view_user_transactions'
    ACTION_VIEW_LEDGER = 'view_ledger'
    ACTION_VIEW_AUDIT_LOGS = 'view_audit_logs'
    ACTION_VERIFY_TRANSACTION = 'verify_transaction'
    ACTION_VIEW_USER_PROFILE = 'view_user_profile'
    
    ACTION_CHOICES = [
        (ACTION_VIEW_ALL_TRANSACTIONS, 'View All Transactions'),
        (ACTION_VIEW_USER_TRANSACTIONS, 'View User Transactions'),
        (ACTION_VIEW_LEDGER, 'View Ledger'),
        (ACTION_VIEW_AUDIT_LOGS, 'View Audit Logs'),
        (ACTION_VERIFY_TRANSACTION, 'Verify Transaction'),
        (ACTION_VIEW_USER_PROFILE, 'View User Profile'),
    ]
    
    id = models.AutoField(primary_key=True)
    admin = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='audit_logs_created'
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )
    
    # Target of the action (if applicable)
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs_targeted'
    )
    target_transaction_id = models.IntegerField(
        null=True,
        blank=True
    )
    
    # Additional details
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context about the action"
    )
    
    # IP address and user agent for tracking
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        null=True,
        blank=True
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        target = f" -> {self.target_user.email}" if self.target_user else ""
        return f"Audit-{self.id}: {self.admin.email} {self.action}{target} at {self.created_at}"
    
    @classmethod
    def log_admin_action(
        cls,
        admin: User,
        action: str,
        target_user: User = None,
        target_transaction_id: int = None,
        details: dict = None,
        request=None
    ):
        """
        Create an audit log entry for an admin action.
        
        Args:
            admin: The admin user performing the action
            action: The type of action (from ACTION_CHOICES)
            target_user: The user being accessed (if applicable)
            target_transaction_id: The transaction ID being accessed (if applicable)
            details: Additional context as dictionary
            request: Django request object to extract IP/user agent
        """
        log_data = {
            'admin': admin,
            'action': action,
            'target_user': target_user,
            'target_transaction_id': target_transaction_id,
            'details': details or {}
        }
        
        if request:
            # Extract IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                log_data['ip_address'] = x_forwarded_for.split(',')[0].strip()
            else:
                log_data['ip_address'] = request.META.get('REMOTE_ADDR')
            
            # Extract user agent
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(**log_data)
