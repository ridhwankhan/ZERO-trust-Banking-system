from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.users.models import User
from apps.transactions.models import Ledger


class Command(BaseCommand):
    help = 'Initialize user balances for testing'

    def add_arguments(self, parser):
        parser.add_argument('--amount', type=str, default='1000.00',
                           help='Initial balance amount (default: 1000.00)')
        parser.add_argument('--user-id', type=int,
                           help='Specific user ID to initialize (optional)')

    def handle(self, *args, **options):
        amount = Decimal(options['amount'])
        user_id = options.get('user_id')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                ledger, created = Ledger.objects.get_or_create(
                    user=user, 
                    defaults={'balance': amount}
                )
                if not created:
                    ledger.balance = amount
                    ledger.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Initialized balance for {user.email}: {amount}'
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} not found')
                )
        else:
            # Initialize all users
            for user in User.objects.all():
                ledger, created = Ledger.objects.get_or_create(
                    user=user, 
                    defaults={'balance': amount}
                )
                if not created:
                    ledger.balance = amount
                    ledger.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Initialized balance for {user.email}: {amount}'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS('Balance initialization complete!'))
