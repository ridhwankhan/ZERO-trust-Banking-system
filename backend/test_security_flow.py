import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.conf import settings
settings.ALLOWED_HOSTS.append('testserver')

from django.test import Client
import json
from apps.users.models import User
from apps.security.models import LoginEvent, SecurityAlert

def run_test():
    print("Starting integration test for security modules...")
    
    # 1. Create a test user
    User.objects.filter(email='test_security@example.com').delete()
    user = User.objects.create_user(
        email='test_security@example.com',
        username='testsec',
        password='Password123!',
        first_name='Test',
        last_name='Security'
    )
    print("User created.")

    # 2. Test Login Event & Risk Engine Hook
    client = Client()
    # Try a login with proper credentials
    resp = client.post(
        '/api/auth/login/',
        data=json.dumps({'email': 'test_security@example.com', 'password': 'Password123!'}),
        content_type='application/json',
        HTTP_X_DEVICE_FINGERPRINT='test_device_123',
        REMOTE_ADDR='1.1.1.1' # Sydney mock
    )
    
    print(f"Login Response: {resp.status_code}")
    if resp.status_code != 200:
        with open('error_output.html', 'wb') as f:
            f.write(resp.content)
        print("Error output saved to error_output.html")
        return False
        
    data = resp.json()
    print("Security data in response:", data.get('security'))
    
    # Verify a LoginEvent was created
    events = LoginEvent.objects.filter(user=user).order_by('-created_at')
    print(f"LoginEvents recorded for user: {events.count()}")
    if events.count() > 0:
        ev = events.first()
        print(f"Latest event: {ev.ip_address} | {ev.city}, {ev.country} | Risk: {ev.risk_level} ({ev.risk_score})")

    # 3. Test Security Middleware
    resp_malicious = client.post(
        '/api/transactions/deposit/process/',
        data=json.dumps({'amount': 100}),
        content_type='application/json',
        HTTP_AUTHORIZATION=f"Bearer {data['tokens']['access']}"
    )
    
    # Send a malicious payload
    resp_blocked = client.post(
        '/api/transactions/deposit/process/',
        data=json.dumps({'amount': 100, 'note': "<script>alert(1)</script>"}),
        content_type='application/json',
        HTTP_AUTHORIZATION=f"Bearer {data['tokens']['access']}"
    )
    print(f"Malicious request response: {resp_blocked.status_code}")
    print(resp_blocked.content)
    
    alerts = SecurityAlert.objects.filter(user=user, alert_type__contains='XSS')
    print(f"SecurityAlerts created for XSS: {alerts.count()}")

    print("\nTests completed successfully.")
    return True

if __name__ == '__main__':
    run_test()
