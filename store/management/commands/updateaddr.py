from django.core.management.base import BaseCommand
from payment.models import Balance

class Command(BaseCommand):
    help = 'Reset the address of the balance'
    def handle(self, *args, **options):
        # Use update() to perform a single efficient database query
        updated_count = Balance.objects.all().update(address=None)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully reset the address of {updated_count} balances'
            )
        )