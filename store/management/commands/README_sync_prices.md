# Sync Invoice Prices Management Command

This Django management command efficiently synchronizes `invoice.received` values with their corresponding `product.price` values.

## Usage

```bash
python manage.py sync_invoice_prices [--batch-size <size>] [--dry-run] [--filter-null-prices]
```

## Parameters

- `--batch-size` (optional): Number of records to process in each batch (default: 1000)
- `--dry-run` (optional): Show what would be updated without making actual changes
- `--filter-null-prices` (optional): Skip invoices where product.price is null

## Examples

### Basic sync (update all invoices):
```bash
python manage.py sync_invoice_prices
```

### Dry run to see what would be changed:
```bash
python manage.py sync_invoice_prices --dry-run
```

### Process with smaller batches for large datasets:
```bash
python manage.py sync_invoice_prices --batch-size 500
```

### Skip invoices with null product prices:
```bash
python manage.py sync_invoice_prices --filter-null-prices
```

### Combine options:
```bash
python manage.py sync_invoice_prices --dry-run --filter-null-prices --batch-size 250
```

## Performance Features

### **Database Efficiency:**
- **select_related('product')**: Eliminates N+1 queries by fetching product data in one query
- **bulk_update()**: Updates multiple records in a single database operation
- **Batch Processing**: Processes records in configurable batches (default 1000) to manage memory
- **Transaction Atomic**: Wraps updates in database transactions for consistency

### **Runtime Efficiency:**
- **Smart Filtering**: Only updates invoices where `received != product.price`
- **Progress Tracking**: Shows progress every 5 batches to monitor large operations
- **Memory Management**: Processes records in batches to avoid loading all data into memory

### **Safety Features:**
- **Dry Run Mode**: Test the operation without making changes
- **Null Handling**: Options to handle products with null prices
- **Statistics**: Shows sync status and completion metrics

## What Gets Updated

The command sets `invoice.received = product.price` for each invoice where:
- The values are different (`received != product.price`)
- Product price is not null (unless `--filter-null-prices` is used)

## Output

The command provides:
- **Progress Updates**: Real-time progress during processing
- **Summary**: Total updated/skipped count
- **Statistics**: Post-update sync percentage and data health metrics
- **Dry Run Preview**: Examples of what would be changed (first 5 per batch)

## Use Cases

1. **Data Migration**: After importing invoice data that needs price sync
2. **Price Updates**: After bulk product price changes
3. **Data Cleanup**: Ensuring invoice amounts match current product prices
4. **Regular Maintenance**: Keeping financial data consistent

## Performance Expectations

- **Small datasets** (< 1000 invoices): Nearly instantaneous
- **Medium datasets** (1000-10,000 invoices): 1-5 seconds  
- **Large datasets** (10,000+ invoices): Scales linearly with batch processing

The command is optimized to handle datasets of any size efficiently without memory issues. 