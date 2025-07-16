# Generate Random Invoices Management Command

This Django management command allows you to generate random invoices with customizable parameters.

## Usage

```bash
python manage.py generate_random_invoices <count> --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD> [--status <status_code>] [--user <email_or_username>]
```

## Parameters

- `count` (required): Number of invoices to generate
- `--start-date` (required): Start date in YYYY-MM-DD format
- `--end-date` (required): End date in YYYY-MM-DD format  
- `--status` (optional): Specific status code to use for all invoices
  - `-1`: Not Started
  - `0`: Unconfirmed
  - `1`: Partially Confirmed
  - `2`: Confirmed
- `--user` (optional): Specific customer email or username to use for all invoices

## Examples

### Generate 100 random invoices for January 2024:
```bash
python manage.py generate_random_invoices 100 --start-date 2024-01-01 --end-date 2024-01-31
```

### Generate 50 invoices with "Confirmed" status for Q1 2024:
```bash
python manage.py generate_random_invoices 50 --start-date 2024-01-01 --end-date 2024-03-31 --status 2
```

### Generate 25 invoices for a specific week:
```bash
python manage.py generate_random_invoices 25 --start-date 2024-01-15 --end-date 2024-01-21
```

### Generate 75 invoices for a specific user by email:
```bash
python manage.py generate_random_invoices 75 --start-date 2024-01-01 --end-date 2024-01-31 --user john@example.com
```

### Generate 30 confirmed invoices for a specific user by username:
```bash
python manage.py generate_random_invoices 30 --start-date 2024-02-01 --end-date 2024-02-28 --status 2 --user johndoe
```

## What Gets Randomized

The command automatically randomizes the following fields:

- **Product**: Randomly selected from active products (`Status=True`)
- **Customer**: Randomly selected from active customers (`is_active=True`) or specific user if `--user` is provided
- **Date**: Random date/time between your specified start and end dates
- **Order ID**: Generated in format `INV-XXXXXXXXXXXX` (12 random characters)
- **Status**: Random status (-1 to 2) unless you specify a fixed status
- **BTC Value**: Random value between 0.001 and 1.0 BTC
- **Received**: Random value between 0.0 and 0.5 BTC
- **Address**: Random Bitcoin-like address (or None)
- **Transaction ID**: Random 64-character transaction ID (or None)
- **RBF**: Random integer 0-2 (or None)
- **Sold**: Random True/False
- **Decrypted**: Random True/False

## Requirements

- At least one active product (`Status=True`) must exist
- At least one active customer (`is_active=True`) must exist (unless `--user` is specified)
- If `--user` is provided, the specified customer must exist and be active
- Start date must be before or equal to end date

## Output

The command provides progress updates every 100 invoices created and shows a success message with the total count upon completion. 