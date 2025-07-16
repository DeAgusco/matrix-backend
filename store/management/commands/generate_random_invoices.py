import random
import string
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from payment.models import Invoice
from accounts.models import Customer
from store.models import Product


class Command(BaseCommand):
    help = 'Generate random invoices with specified count and date range'

    def add_arguments(self, parser):
        parser.add_argument(
            'count',
            type=int,
            help='Number of invoices to generate'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            required=True,
            help='Start date in YYYY-MM-DD format'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            required=True,
            help='End date in YYYY-MM-DD format'
        )
        parser.add_argument(
            '--status',
            type=int,
            choices=[-1, 0, 1, 2],
            help='Specific status to use (optional, otherwise random)'
        )

    def handle(self, *args, **options):
        count = options['count']
        start_date_str = options['start_date']
        end_date_str = options['end_date']
        fixed_status = options.get('status')

        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            raise CommandError('Date format should be YYYY-MM-DD')

        if start_date > end_date:
            raise CommandError('Start date cannot be after end date')

        # Get available products and customers
        products = list(Product.objects.filter(Status=True))
        customers = list(Customer.objects.filter(is_active=True))

        if not products:
            raise CommandError('No active products found')
        if not customers:
            raise CommandError('No active customers found')

        # Status choices
        status_choices = [-1, 0, 1, 2]

        # Generate invoices
        invoices_created = 0
        for i in range(count):
            try:
                # Random date between start and end
                random_date = self.random_date(start_date, end_date)
                random_datetime = timezone.make_aware(
                    datetime.combine(random_date, datetime.min.time())
                )

                # Random product and customer
                product = random.choice(products)
                customer = random.choice(customers)

                # Generate random data
                order_id = self.generate_order_id()
                status = fixed_status if fixed_status is not None else random.choice(status_choices)
                
                # Create invoice
                invoice = Invoice.objects.create(
                    product=product,
                    status=status,
                    order_id=order_id,
                    address=self.generate_random_address(),
                    btcvalue=round(random.uniform(0.001, 1.0), 6),
                    received=round(random.uniform(0.0, 0.5), 6),
                    txid=self.generate_txid() if random.choice([True, False]) else None,
                    rbf=random.randint(0, 2) if random.choice([True, False]) else None,
                    created_at=random_datetime,
                    created_by=customer,
                    sold=random.choice([True, False]),
                    decrypted=random.choice([True, False])
                )
                
                invoices_created += 1
                
                if invoices_created % 100 == 0:
                    self.stdout.write(f'Created {invoices_created} invoices...')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating invoice {i+1}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {invoices_created} random invoices '
                f'between {start_date} and {end_date}'
            )
        )

    def random_date(self, start_date, end_date):
        """Generate a random date between start_date and end_date"""
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between + 1)
        return start_date + timedelta(days=random_days)

    def generate_order_id(self):
        """Generate a random order ID"""
        return 'INV-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

    def generate_random_address(self):
        """Generate a random Bitcoin-like address"""
        if random.choice([True, False]):
            # Generate a random address
            address_chars = string.ascii_letters + string.digits
            return ''.join(random.choices(address_chars, k=random.randint(26, 35)))
        return None

    def generate_txid(self):
        """Generate a random transaction ID"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=64)) 