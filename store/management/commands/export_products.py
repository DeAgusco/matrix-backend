from django.core.management.base import BaseCommand
from store.models import Product
import csv

class Command(BaseCommand):
    help = 'Export products to a data file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the output data file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        # Get all field names from the Product model (excluding category since we'll handle it specially)
        field_names = [field.name for field in Product._meta.fields if field.name != 'category']
        
        # Create a custom header with category_name and category_location instead of just category
        header = ['category_name', 'category_location'] + field_names
        
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            
            # Use select_related to efficiently fetch category data in a single query
            products = Product.objects.all().select_related('category')
            
            for product in products:
                # Create row with category name and location first, then all other fields
                row = [
                    product.category.name,  # Use category name instead of ID
                    product.category.location,  # Add category location
                ]
                
                # Add all other product fields
                for field in field_names:
                    row.append(getattr(product, field))
                
                writer.writerow(row)

        self.stdout.write(self.style.SUCCESS(f'Successfully exported {products.count()} products with category details.'))
