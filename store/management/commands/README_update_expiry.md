# Update Product Expiry Management Command

This management command updates product expiry values (`Product.exp`) by adding a specified number of years while preserving the original format. It is designed for large datasets and prioritizes transactional safety and database efficiency.

## Usage

```bash
python manage.py update_product_expiry [--years <years>] [--batch-size <size>] [--dry-run] [--show-samples <count>]
```

## Parameters

- `--years` (optional): Number of years to add to each expiry value (default: 3)
- `--batch-size` (optional): Number of products to include in each bulk update batch (default: 1000)
- `--dry-run` (optional): Show what would change without saving any updates
- `--show-samples` (optional): Number of sample updates to display during a dry run (default: 5)

## Supported Expiry Formats

The command recognizes and preserves these formats:

### Text Month Formats (NEW):
- `Aug-29`, `August-29` (month abbreviation/full name with dash and 2-digit year)
- `Aug-2029`, `August-2029` (month abbreviation/full name with dash and 4-digit year)
- `Aug/29`, `August/29` (month abbreviation/full name with slash and 2-digit year)
- `Aug/2029`, `August/2029` (month abbreviation/full name with slash and 4-digit year)

Supports all month abbreviations (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec) and full names. Preserves original capitalization.

### Numeric Formats:
- `MM/YY`, `M/YY`, `MM-YY`, `M-YY`
- `MM/YYYY`, `M/YYYY`, `MM-YYYY`, `M-YYYY`
- `YYYY/MM`, `YYYY-MM`
- `MMYY`, `MMYYYY` (no separator)

Values outside these patterns are skipped and reported.

## Examples

### Default behaviour (add 3 years):
```bash
python manage.py update_product_expiry
```

### Add 5 years to all expiry dates:
```bash
python manage.py update_product_expiry --years 5
```

### Preview changes without committing:
```bash
python manage.py update_product_expiry --dry-run
```

### Process using smaller batches:
```bash
python manage.py update_product_expiry --batch-size 250
```

### Dry run with additional sample output:
```bash
python manage.py update_product_expiry --dry-run --show-samples 10
```

## Performance Features

- **Bulk Updates**: Uses `bulk_update` to minimize database round trips
- **Chunked Iteration**: Processes records in batches to limit memory usage
- **Transactional Safety**: Wraps updates in a single atomic transaction (automatically rolled back during dry runs)
- **Format Preservation**: Maintains the original delimiter (`/` or `-`) and year length (2 or 4 digits)

## Output

The command reports:

- Total products processed
- Number of expiry values updated
- Number of values skipped (due to unsupported formats)
- Number of values already up to date
- Sample changes during dry runs (configurable)

## Use Cases

- Aligning expiry dates after data imports
- Extending lifespan of product records
- Periodic maintenance to ensure expiry data stays current

## Notes

- Products without an expiry value (`exp` empty or null) are ignored
- Expiry values that cannot be parsed are skipped and counted in the summary
- When using `--dry-run`, all changes are rolled back automatically
