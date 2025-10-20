# Universal Data Normalization Specification (UDNS) v1.0

A comprehensive Python implementation of the Universal Data Normalization Specification (UDNS), providing standardized parsing and normalization of unstructured text data across multiple domains.

## Overview

UDNS offers a unified approach to extract, transform, and represent data from various sources while preserving semantic meaning and maintaining interoperability. This implementation supports multiple entity types including invoices, addresses, contacts, products, orders, and personal information.

## Features

- **Multi-domain Support**: Handles invoices, addresses, contacts, products, people, and more
- **Standards Compliance**: Implements ISO 8601 (dates), ISO 4217 (currency), E.164 (phone numbers), and ISO 3166-1 (country codes)
- **Automatic Detection**: Intelligently detects entity types from input text
- **Schema Validation**: Built-in JSON schema validation for all entity types
- **Batch Processing**: Process multiple inputs efficiently
- **Extensible Architecture**: Easy to add new entity types and parsers
- **CLI Interface**: Command-line tool for quick processing and validation

## Installation

### From Source

```bash
git clone https://github.com/bateikoEd/experimets_genai.git
cd experimets_genai
pip install -r requirements.txt
pip install -e .
```

### Dependencies

- Python 3.8+
- jsonschema (for validation)
- phonenumbers (for phone number parsing)

## Quick Start

### Basic Usage

```python
from udns import UDNSProcessor, EntityType

# Initialize processor
processor = UDNSProcessor()

# Process invoice data
invoice_text = "Invoice #A-1027 | Vendor: Globex Ltd. | Date: 03/09/2025 | Total: £2,345.70"
result = processor.process(invoice_text, EntityType.INVOICE)

print(result.to_dict())
# Output:
# {
#   "entity_type": "invoice",
#   "attributes": {
#     "invoice_number": "A-1027",
#     "vendor_name": "Globex Ltd.",
#     "invoice_date": "2025-09-03",
#     "total_amount": 2345.70,
#     "currency_code": "GBP"
#   },
#   "metadata": {
#     "confidence": 0.9,
#     "parser_version": "1.0.0"
#   }
# }
```

### Automatic Type Detection

```python
# Let UDNS detect the entity type automatically
contact_text = "Support: (044) 123-45-67 ext 123, help@example.ua"
result = processor.process(contact_text)  # Auto-detects as CONTACT

print(f"Detected type: {result.entity_type.value}")
print(f"Phone: {result.attributes.get('phone_e164')}")
print(f"Email: {result.attributes.get('email')}")
```

### Batch Processing

```python
inputs = [
    {
        'id': 'inv1',
        'text': 'Invoice #123 from ACME Corp - Total: $500.00',
        'entity_type': 'invoice'
    },
    {
        'id': 'contact1',
        'text': 'John Doe: john@company.com, +1-555-1234'
    }
]

results = processor.process_batch(inputs)
for result in results:
    if result['success']:
        print(f"{result['id']}: ✅ Processed")
    else:
        print(f"{result['id']}: ❌ {result['error']}")
```

## Command Line Interface

The UDNS CLI provides a convenient way to process text from the command line:

### Basic Usage

```bash
# Process single text input
udns -t "Invoice #123 from ACME Corp - Total: $500.00"

# Specify entity type explicitly
udns -t "John Doe, 123 Main St" --type address

# Process file
udns -f input.txt -o output.json --pretty

# List supported entity types
udns --list-types

# Validate against examples
udns --validate-examples
```

### Batch Processing

```bash
# Process JSON batch file
udns -f batch_inputs.json --batch -o results.json
```

Example batch input file:
```json
[
  {
    "id": "item1",
    "text": "Invoice #A-1027 | Vendor: Globex Ltd. | Total: £2,345.70",
    "entity_type": "invoice"
  },
  {
    "id": "item2", 
    "text": "Contact: help@example.com, +380441234567"
  }
]
```

## Supported Entity Types

| Entity Type | Description | Example Input |
|-------------|-------------|---------------|
| `invoice` | Invoice and billing data | "Invoice #A-1027 &#124; Vendor: Globex Ltd. &#124; Total: £2,345.70" |
| `address` | Postal addresses | "Bill To: John Doe, 123 Main St, City 12345, Country" |
| `contact` | Contact information | "Support: (044) 123-45-67, help@example.com" |
| `product` | Product information | "Arabica Coffee Beans 1kg — Price: €19,90" |
| `person` | Personal information | "Prof. François L'Écuyer (CTO) — francois@example.fr" |
| `order` | Order and line items | "Items: 2x SKU-1001 (Blue T-Shirt M), Ship by: 2025-10-22" |
| `payment` | Payment transactions | "Paid: 5,000 JPY via card (Auth: 9ZK12)" |
| `event` | Calendar events | "Standup — 20 Oct 2025, 09:30–09:50 Europe/Kyiv" |
| `log_event` | Log entries | "WARN [Payments] 2025/09/17 08:45:10 UTC user=984" |
| `spec` | Measurements/specs | "Spec: 10 in × 6 in × 2.5 in; weight 1 lb 4 oz" |

## Data Standards

UDNS follows international standards for data representation:

- **Dates**: ISO 8601 format (`YYYY-MM-DD`, `YYYY-MM-DDTHH:mm:ssZ`)
- **Currency**: ISO 4217 three-letter codes (`USD`, `EUR`, `GBP`)
- **Phone Numbers**: E.164 international format (`+380441234567`)
- **Country Codes**: ISO 3166-1 alpha-3 (`USA`, `GBR`, `UKR`)
- **Email**: RFC 5322 compliant addresses

## Architecture

### Core Components

1. **Core Module** (`udns/core.py`): Data structures and base classes
2. **Normalizers** (`udns/normalizers.py`): Standard data type conversion
3. **Parsers** (`udns/parsers.py`): Domain-specific text parsing
4. **Validators** (`udns/validators.py`): JSON schema validation
5. **Processor** (`udns/processor.py`): Main orchestration logic

### Universal Wrapper Format

All normalized outputs follow this structure:

```json
{
  "entity_type": "string",
  "attributes": {
    // Domain-specific normalized data
  },
  "metadata": {
    "confidence": 0.95,
    "parser_version": "1.0.0",
    // Additional processing metadata
  }
}
```

## Extending UDNS

### Adding Custom Parsers

```python
from udns.parsers import DomainParser
from udns.core import EntityType, NormalizedEntity, Metadata

class CustomParser(DomainParser):
    def parse(self, input_text: str, **kwargs) -> NormalizedEntity:
        # Your parsing logic here
        attributes = {"custom_field": "value"}
        metadata = Metadata(confidence=0.9)
        
        return NormalizedEntity(
            entity_type=EntityType.CUSTOM,  # Define new entity type
            attributes=attributes,
            metadata=metadata
        )

# Register with processor
processor = UDNSProcessor()
processor.add_parser(EntityType.CUSTOM, CustomParser())
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest test_udns.py -v

# Run with coverage
pytest test_udns.py --cov=udns --cov-report=html
```

Validate against provided examples:

```bash
python test_udns.py  # Runs validation against temp.json examples
```

## Performance

UDNS is designed for efficiency:

- **Single Processing**: ~1-5ms per input (depending on complexity)
- **Batch Processing**: Optimized for bulk operations
- **Memory Usage**: Low memory footprint with streaming support
- **Confidence Scoring**: Fast heuristic-based confidence calculation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/bateikoEd/experimets_genai.git
cd experimets_genai

# Install in development mode
pip install -e .[dev]

# Run linting
black udns/
flake8 udns/
mypy udns/
```

## Examples

See the `data/temp.json` file for comprehensive examples of each entity type and their expected normalized outputs.

## License

MIT License - see LICENSE file for details.

## Changelog

### v1.0.0 (2025-10-20)
- Initial release
- Support for 10 entity types
- CLI interface
- Comprehensive test suite
- Full OpenSpec proposal compliance

## Support

For issues, questions, or contributions, please use the GitHub repository:
- Issues: https://github.com/bateikoEd/experimets_genai/issues
- Discussions: https://github.com/bateikoEd/experimets_genai/discussions

## Roadmap

- [ ] Additional entity types (locations, organizations, etc.)
- [ ] Machine learning-based confidence scoring
- [ ] REST API interface
- [ ] Visualization tools for normalized data
- [ ] Performance optimizations
- [ ] Additional output formats (XML, YAML, etc.)