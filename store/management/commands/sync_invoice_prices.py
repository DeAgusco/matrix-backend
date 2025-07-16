from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, models
from payment.models import Invoice


class Command(BaseCommand):
    help = 'Sync invoice.received field with product.price for all invoices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch (default: 1000)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--filter-null-prices',
            action='store_true',
            help='Skip invoices where product.price is null'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        filter_null_prices = options['filter_null_prices']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Build queryset with optimized joins
        queryset = Invoice.objects.select_related('product').all()
        
        if filter_null_prices:
            queryset = queryset.exclude(product__price__isnull=True)

        total_invoices = queryset.count()
        self.stdout.write(f'Found {total_invoices} invoices to process')

        if total_invoices == 0:
            self.stdout.write(self.style.SUCCESS('No invoices to update'))
            return

        updated_count = 0
        skipped_count = 0
        processed_count = 0

        # Process in batches for memory efficiency
        with transaction.atomic():
            while processed_count < total_invoices:
                # Get batch with offset
                batch = list(queryset[processed_count:processed_count + batch_size])
                
                if not batch:
                    break

                # Prepare list of invoices to update
                invoices_to_update = []
                
                for invoice in batch:
                    product_price = invoice.product.price
                    current_received = invoice.received

                    # Skip if product price is null and we're filtering
                    if product_price is None and filter_null_prices:
                        skipped_count += 1
                        continue

                    # Only update if values are different
                    if current_received != product_price:
                        invoice.received = product_price
                        invoices_to_update.append(invoice)

                # Bulk update if we have invoices to update
                if invoices_to_update and not dry_run:
                    Invoice.objects.bulk_update(
                        invoices_to_update, 
                        ['received'], 
                        batch_size=batch_size
                    )
                    updated_count += len(invoices_to_update)
                elif invoices_to_update and dry_run:
                    # In dry run, just count what would be updated
                    updated_count += len(invoices_to_update)
                    for invoice in invoices_to_update[:5]:  # Show first 5 examples
                        self.stdout.write(
                            f'Would update Invoice {invoice.id}: '
                            f'received {invoice.received} -> {invoice.product.price}'
                        )
                    if len(invoices_to_update) > 5:
                        self.stdout.write(f'... and {len(invoices_to_update) - 5} more in this batch')

                processed_count += len(batch)

                # Progress update every batch
                if processed_count % (batch_size * 5) == 0 or processed_count >= total_invoices:
                    self.stdout.write(
                        f'Processed {processed_count}/{total_invoices} invoices '
                        f'({(processed_count/total_invoices)*100:.1f}%)'
                    )

        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN COMPLETE: Would update {updated_count} invoices, '
                    f'skip {skipped_count} invoices'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} invoices with product prices. '
                    f'Skipped {skipped_count} invoices.'
                )
            )

        # Additional statistics
        if not dry_run:
            self.show_statistics()

    def show_statistics(self):
        """Show useful statistics after the update"""
        total_invoices = Invoice.objects.count()
        invoices_with_received = Invoice.objects.exclude(received__isnull=True).count()
        invoices_matching_price = Invoice.objects.filter(
            received=models.F('product__price')
        ).count()

        self.stdout.write('\n--- Statistics ---')
        self.stdout.write(f'Total invoices: {total_invoices}')
        self.stdout.write(f'Invoices with received value: {invoices_with_received}')
        self.stdout.write(f'Invoices where received = product.price: {invoices_matching_price}')

        if total_invoices > 0:
            sync_percentage = (invoices_matching_price / total_invoices) * 100
            self.stdout.write(f'Sync percentage: {sync_percentage:.1f}%') 