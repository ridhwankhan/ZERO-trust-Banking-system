#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.users.models import User

# Keep in sync with AdminLoginView / AuthorityLoginView hardcoded demos
admin_email = 'admin@fiducia.bd'
admin_password = 'admin123'
authority_email = 'authority@fiducia.bd'
authority_password = 'authority123'

admin_user, _ = User.objects.get_or_create(
    email=admin_email,
    defaults={
        'username': 'admin',
        'role': 'admin',
        'is_staff': True,
        'is_active': True,
        'is_verified': True,
        'kyc_status': User.KYC_VERIFIED,
        'balance': 1000000.00,
    },
)
admin_user.role = 'admin'
admin_user.is_staff = True
admin_user.set_password(admin_password)
admin_user.save()
print(f'Admin ready: {admin_email} / {admin_password}')

authority_user, _ = User.objects.get_or_create(
    email=authority_email,
    defaults={
        'username': 'authority',
        'role': 'authority',
        'is_staff': True,
        'is_active': True,
        'is_verified': True,
        'kyc_status': User.KYC_VERIFIED,
        'balance': 500000.00,
    },
)
authority_user.role = 'authority'
authority_user.is_staff = True
authority_user.set_password(authority_password)
authority_user.save()
print(f'Authority ready: {authority_email} / {authority_password}')
