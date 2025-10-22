# CLI Testing Guide

The `test_extractors.py` script provides a comprehensive CLI for testing the data normalization SDK extractors.

## Usage Examples

### 1. Test with Specific Text (Full Pipeline)
```bash
python test_extractors.py --text "Invoice #A-1027 | Vendor: Globex Ltd. | Date: 03/09/2025 | Total: £2,345.70 (VAT 20%)"
```

### 2. Test Specific Extractor
```bash
python test_extractors.py --extractor address --text "Bill To: John Doe, 123 Main St, New York, NY 10001, USA"
```

### 3. Test with Example Data
```bash
python test_extractors.py --examples
```

### 4. Interactive Mode
```bash
python test_extractors.py --interactive
```

## Available Extractors

- **invoice**: Invoice numbers, vendors, dates, amounts, tax rates
- **address**: Names, street addresses, cities, countries, postal codes  
- **contact**: Phone numbers (E.164), emails, extensions
- **product**: Names, weights, prices, currencies, categories
- **order**: Line items, SKUs, quantities, shipping dates

## Test Data Examples

### Invoice
```
Invoice #A-1027 | Vendor: Globex Ltd. | Date: 03/09/2025 | Total: £2,345.70 (VAT 20%)
```

### Address  
```
Bill To: Nguyen Thi Lan, 12/5 Tran Hung Dao, Dist. 1, Ho Chi Minh City 700000, Vietnam
```

### Contact
```
Support: (044) 123-45-67 ext 123, help[at]example.ua
```

### Product
```
Name: Arabica Coffee Beans 1kg — Price: €19,90 — Category: Grocery > Coffee & Tea
```

### Order
```
Items: 2 x SKU-1001 (Blue T-Shirt M), 1x SKU-2020 (Jeans 32/32); Ship by: 2025-10-22
```

## Output Format

The CLI provides rich formatted output including:

- ✅/❌ Success/failure indicators
- 🏷️ Entity type detection
- 📊 Confidence scores 
- 🔄 Applied transformations
- 📋 Structured extracted data (JSON format)
- 🎯 Supported entity types per extractor

## Interactive Mode Commands

- `quit` or `exit` - Exit the interactive mode
- `examples` - Run tests with all example data
- Any text input - Process with SDK pipeline

## CLI Options

- `--text TEXT, -t TEXT` - Text to extract data from
- `--extractor EXTRACTOR, -e EXTRACTOR` - Test specific extractor 
- `--examples` - Test with example data from data_examples.json
- `--interactive, -i` - Start interactive testing mode
- `--json` - Output results in JSON format (future feature)
- `--help, -h` - Show help message