#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.users.models import User

# Create Admin User
admin_email = "admin@example.com"
admin_password = "Admin@12345"

if not User.objects.filter(email=admin_email).exists():
    admin_user = User.objects.create(
        email=admin_email,
        username="admin",
        role='admin',
        is_staff=True,
        is_superuser=False,
        is_active=True,
        balance=1000000.00
    )
    admin_user.set_password(admin_password)
    admin_user.save()
    print(f"✅ Admin user created: {admin_email}")
else:
    print(f"⚠️  Admin user already exists: {admin_email}")

# Create Authority User
authority_email = "authority@example.com"
authority_password = "Authority@12345"

if not User.objects.filter(email=authority_email).exists():
    authority_user = User.objects.create(
        email=authority_email,
        username="authority",
        role='authority',
        is_staff=True,
        is_superuser=False,
        is_active=True,
        balance=500000.00
    )
    authority_user.set_password(authority_password)
    authority_user.save()
    print(f"✅ Authority user created: {authority_email}")
else:
    print(f"⚠️  Authority user already exists: {authority_email}")

print("\n" + "="*50)
print("📝 LOGIN CREDENTIALS FOR ADMIN & AUTHORITY")
print("="*50)
print(f"\n🔐 Admin Account:")
print(f"   Email: {admin_email}")
print(f"   Password: {admin_password}")
print(f"   Role: admin")

print(f"\n🏛️  Authority Account:")
print(f"   Email: {authority_email}")
print(f"   Password: {authority_password}")
print(f"   Role: authority")

print("\n" + "="*50)
print("Go to http://localhost:5174/login and try these!")
print("="*50 + "\n")
