import re
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from store.models import Product

# Month name mappings (abbreviations and full names)
MONTH_MAP = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12,
}


class Command(BaseCommand):
    help = (
        'Add a specified number of years to product expiry values (Product.exp) '
        'using efficient bulk updates.'
    )

    EXP_PATTERNS = (
        # Text month abbreviations/full names with dash and 2-digit year (e.g., Aug-29, August-29)
        {
            'regex': re.compile(r'^(?P<month_text>[A-Za-z]+)-(?P<year>\d{2})$', re.IGNORECASE),
            'year_length': 2,
            'separator': '-',
            'month_first': True,
            'month_type': 'text',
        },
        # Text month abbreviations/full names with dash and 4-digit year (e.g., Aug-2029, August-2029)
        {
            'regex': re.compile(r'^(?P<month_text>[A-Za-z]+)-(?P<year>\d{4})$', re.IGNORECASE),
            'year_length': 4,
            'separator': '-',
            'month_first': True,
            'month_type': 'text',
        },
        # Text month abbreviations/full names with slash and 2-digit year (e.g., Aug/29, August/29)
        {
            'regex': re.compile(r'^(?P<month_text>[A-Za-z]+)/(?P<year>\d{2})$', re.IGNORECASE),
            'year_length': 2,
            'separator': '/',
            'month_first': True,
            'month_type': 'text',
        },
        # Text month abbreviations/full names with slash and 4-digit year (e.g., Aug/2029, August/2029)
        {
            'regex': re.compile(r'^(?P<month_text>[A-Za-z]+)/(?P<year>\d{4})$', re.IGNORECASE),
            'year_length': 4,
            'separator': '/',
            'month_first': True,
            'month_type': 'text',
        },
        # MM/YY or M/YY (with / separator)
        {
            'regex': re.compile(r'^(?P<month>\d{1,2})/(?P<year>\d{2})$'),
            'year_length': 2,
            'separator': '/',
            'month_first': True,
            'month_type': 'numeric',
        },
        # MM-YY or M-YY (with - separator)
        {
            'regex': re.compile(r'^(?P<month>\d{1,2})-(?P<year>\d{2})$'),
            'year_length': 2,
            'separator': '-',
            'month_first': True,
            'month_type': 'numeric',
        },
        # MM/YYYY or M/YYYY (with / separator)
        {
            'regex': re.compile(r'^(?P<month>\d{1,2})/(?P<year>\d{4})$'),
            'year_length': 4,
            'separator': '/',
            'month_first': True,
            'month_type': 'numeric',
        },
        # MM-YYYY or M-YYYY (with - separator)
        {
            'regex': re.compile(r'^(?P<month>\d{1,2})-(?P<year>\d{4})$'),
            'year_length': 4,
            'separator': '-',
            'month_first': True,
            'month_type': 'numeric',
        },
        # YYYY/MM (with / separator, year first)
        {
            'regex': re.compile(r'^(?P<year>\d{4})/(?P<month>\d{1,2})$'),
            'year_length': 4,
            'separator': '/',
            'month_first': False,
            'month_type': 'numeric',
        },
        # YYYY-MM (with - separator, year first)
        {
            'regex': re.compile(r'^(?P<year>\d{4})-(?P<month>\d{1,2})$'),
            'year_length': 4,
            'separator': '-',
            'month_first': False,
            'month_type': 'numeric',
        },
        # MMyy (no separator, 2-digit year)
        {
            'regex': re.compile(r'^(?P<month>\d{2})(?P<year>\d{2})$'),
            'year_length': 2,
            'separator': '',
            'month_first': True,
            'month_type': 'numeric',
        },
        # MMYYYY (no separator, 4-digit year)
        {
            'regex': re.compile(r'^(?P<month>\d{2})(?P<year>\d{4})$'),
            'year_length': 4,
            'separator': '',
            'month_first': True,
            'month_type': 'numeric',
        },
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--years',
            type=int,
            default=3,
            help='Number of years to add to each expiry value (default: 3)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of products to include in each bulk update batch (default: 1000)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without saving any updates',
        )
        parser.add_argument(
            '--show-samples',
            type=int,
            default=5,
            help='Number of sample updates to display during a dry run (default: 5)',
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Show sample expiry values from database to debug format issues',
        )
        parser.add_argument(
            '--show-unmatched',
            type=int,
            default=0,
            help='Show N examples of unmatched expiry formats (default: 0)',
        )

    def handle(self, *args, **options):
        years_to_add = options['years']
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        sample_limit = options['show_samples']
        debug = options.get('debug', False)

        if years_to_add <= 0:
            raise CommandError('--years must be a positive integer')
        if batch_size <= 0:
            raise CommandError('--batch-size must be a positive integer')
        if sample_limit < 0:
            raise CommandError('--show-samples cannot be negative')

        queryset = (
            Product.objects.filter(~Q(exp__isnull=True))
            .exclude(exp__exact='')
            .order_by('pk')
        )

        total_candidates = queryset.count()
        if total_candidates == 0:
            self.stdout.write(self.style.SUCCESS('No products with expiry values found.'))
            return

        # Debug mode: show sample expiry values
        if debug:
            self.stdout.write(self.style.WARNING('DEBUG MODE: Showing sample expiry values...'))
            sample_products = queryset[:20]
            unique_formats = {}
            for product in sample_products:
                exp_val = product.exp.strip()
                if exp_val:
                    # Show first 20 unique formats
                    if exp_val not in unique_formats and len(unique_formats) < 20:
                        unique_formats[exp_val] = product.pk
            
            self.stdout.write('')
            self.stdout.write('Sample expiry values found:')
            for exp_val, pk in list(unique_formats.items())[:20]:
                self.stdout.write(f'  Product {pk}: "{exp_val}" (length: {len(exp_val)}, repr: {repr(exp_val)})')
            
            # Test parsing
            self.stdout.write('')
            self.stdout.write('Testing pattern matching:')
            for exp_val in list(unique_formats.keys())[:10]:
                parsed = self._calculate_new_expiry(exp_val, years_to_add)
                status = '✓ MATCHED' if parsed else '✗ NO MATCH'
                self.stdout.write(f'  "{exp_val}": {status}')
                if parsed:
                    self.stdout.write(f'    -> Would become: "{parsed}"')
            return

        self.stdout.write(
            f'Processing {total_candidates} products with non-empty expiry values...'
        )
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: No changes will be committed.'))

        pending_updates = []
        sample_updates = []
        updated_count = 0
        skipped_count = 0
        unchanged_count = 0
        processed_count = 0
        unmatched_samples = []
        show_unmatched = options.get('show_unmatched', 0)

        iterator = queryset.iterator(chunk_size=batch_size)

        try:
            with transaction.atomic():
                for product in iterator:
                    processed_count += 1
                    original_exp = product.exp.strip()
                    new_exp = self._calculate_new_expiry(original_exp, years_to_add)

                    if new_exp is None:
                        skipped_count += 1
                        if show_unmatched > 0 and len(unmatched_samples) < show_unmatched:
                            unmatched_samples.append((product.pk, original_exp))
                        continue

                    if new_exp == original_exp:
                        unchanged_count += 1
                        continue

                    updated_count += 1
                    if dry_run and len(sample_updates) < sample_limit:
                        sample_updates.append((product.pk, original_exp, new_exp))

                    if not dry_run:
                        product.exp = new_exp
                        pending_updates.append(product)

                        if len(pending_updates) >= batch_size:
                            Product.objects.bulk_update(
                                pending_updates,
                                ['exp'],
                                batch_size=batch_size,
                            )
                            pending_updates.clear()

                if not dry_run and pending_updates:
                    Product.objects.bulk_update(
                        pending_updates,
                        ['exp'],
                        batch_size=batch_size,
                    )

                if dry_run:
                    transaction.set_rollback(True)
        except Exception as exc:
            raise CommandError(f'An error occurred during processing: {exc}') from exc

        # Output summary
        self.stdout.write('')
        self.stdout.write('--- Summary ---')
        self.stdout.write(f'Total processed: {processed_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Unchanged (already up to date): {unchanged_count}')
        self.stdout.write(f'Skipped (unrecognized format): {skipped_count}')

        if unmatched_samples:
            self.stdout.write('')
            self.stdout.write('Sample unmatched expiry formats:')
            for pk, exp_val in unmatched_samples:
                self.stdout.write(f'  Product {pk}: "{exp_val}" (repr: {repr(exp_val)}, length: {len(exp_val)})')

        if dry_run and sample_updates:
            self.stdout.write('')
            self.stdout.write('Sample updates:')
            for pk, old, new in sample_updates:
                self.stdout.write(f' - Product {pk}: {old} -> {new}')

        if dry_run and updated_count == 0:
            self.stdout.write(self.style.WARNING('Dry run completed: no changes needed.'))
        elif dry_run:
            self.stdout.write(self.style.SUCCESS('Dry run completed. No database changes made.'))
        else:
            self.stdout.write(self.style.SUCCESS('Expiry values updated successfully.'))

    def _calculate_new_expiry(self, exp_value: str, years_to_add: int) -> Optional[str]:
        """Return the adjusted expiry string or None if it cannot be parsed."""
        if not exp_value:
            return None

        exp_value = exp_value.strip()
        if not exp_value:
            return None

        for pattern in self.EXP_PATTERNS:
            match = pattern['regex'].match(exp_value)
            if not match:
                continue

            month_type = pattern.get('month_type', 'numeric')
            year_str = match.groupdict().get('year')

            # Handle text month names
            if month_type == 'text':
                month_text = match.groupdict().get('month_text')
                if not month_text:
                    continue
                
                month_lower = month_text.lower()
                month = MONTH_MAP.get(month_lower)
                if month is None:
                    continue
                
                # Preserve original capitalization style (first letter capitalized)
                original_month_text = month_text
                
            else:
                # Handle numeric months
                month_str = match.groupdict().get('month')
                if not month_str:
                    continue
                
                try:
                    month = int(month_str)
                except (TypeError, ValueError):
                    continue
                
                if month < 1 or month > 12:
                    continue
                
                original_month_text = None

            try:
                year = int(year_str)
            except (TypeError, ValueError):
                continue

            new_year = year + years_to_add
            year_length = pattern['year_length']
            separator = pattern['separator']
            month_first = pattern['month_first']

            # Handle 2-digit years
            if year_length == 2:
                new_year %= 100
                formatted_year = f"{new_year:02d}"
            else:
                formatted_year = f"{new_year:04d}"

            # Format the output maintaining original structure
            if month_type == 'text':
                # For text months, preserve the original capitalization
                # Capitalize first letter, lowercase the rest
                formatted_month = original_month_text[0].upper() + original_month_text[1:].lower()
            else:
                formatted_month = f"{month:02d}"
            
            if separator:
                if month_first:
                    return f"{formatted_month}{separator}{formatted_year}"
                else:
                    return f"{formatted_year}{separator}{formatted_month}"
            else:
                # No separator case
                if month_first:
                    return f"{formatted_month}{formatted_year}"
                else:
                    return f"{formatted_year}{formatted_month}"

        return None
