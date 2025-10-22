# Domain-Specific Cleaners Specification

## ADDED Requirements

### REQ-DOMAIN-CLEAN-001: Invoice Data Cleaners

#### Description
The system MUST provide specialized cleaners for invoice data that handle invoice numbers, amounts, dates, and vendor names.

#### Scenario: Invoice Number Standardization
```python
from udns.cleaners import InvoiceCleaner

invoice_cleaner = InvoiceCleaner()

# Various invoice number formats
test_cases = [
    "Invoice #A-1027",
    "INV: A1027", 
    "A1027",
    "#A-1027"
]

for case in test_cases:
    result = invoice_cleaner.clean_invoice_number(case)
    # All result in: "A-1027"
```

#### Scenario: Amount and Currency Cleaning
```python
# Clean and standardize monetary amounts
amount_data = {
    "total_amount": "£2,345.67",
    "tax_amount": "$150.00",
    "currency": "GBP"
}

cleaned = invoice_cleaner.clean_amounts(amount_data)
# Result: {"total_amount": 2345.67, "tax_amount": 150.00, "currency": "GBP"}
```

#### Scenario: Invoice Date Normalization
```python
# Clean invoice date formats
date_cases = [
    "03/09/2025",
    "March 9, 2025", 
    "2025-03-09",
    "9-Mar-2025"
]

for date_str in date_cases:
    normalized = invoice_cleaner.clean_invoice_date(date_str)
    # All result in ISO format: "2025-03-09"
```

### REQ-DOMAIN-CLEAN-002: Address Data Cleaners

#### Description
The system MUST provide specialized cleaners for address data that handle street addresses, postal codes, and country information.

#### Scenario: Address Component Cleaning
```python
from udns.cleaners import AddressCleaner

address_cleaner = AddressCleaner()

# Clean street address components
address_data = {
    "street_address": "  123 Main St.  ",
    "district": "Downtown District",
    "city": "New York",
    "postal_code": "10001-1234"
}

cleaned = address_cleaner.clean_address_components(address_data)
# Result: Properly formatted and validated address components
```

#### Scenario: Postal Code Validation and Formatting
```python
# Validate and format postal codes
postal_cases = [
    "10001",
    "10001-1234", 
    "10001 1234",
    "10001-1234-5678"  # Invalid
]

for postal_code in postal_cases:
    result = address_cleaner.clean_postal_code(postal_code, "USA")
    # Valid cases result in standardized format
```

#### Scenario: Country Name and Code Cleaning
```python
# Clean country information
country_data = {
    "country_name": "United States of America",
    "country_code": "US"
}

cleaned = address_cleaner.clean_country_info(country_data)
# Result: {"country_name": "United States", "country_code": "USA"}
```

### REQ-DOMAIN-CLEAN-003: Contact Information Cleaners

#### Description
The system MUST provide specialized cleaners for contact information that handle phone numbers, email addresses, and contact names.

#### Scenario: Phone Number Cleaning and Validation
```python
from udns.cleaners import ContactCleaner

contact_cleaner = ContactCleaner()

# Clean and validate phone numbers
phone_cases = [
    "(044) 123-45-67",
    "0441234567",
    "+380441234567",
    "380441234567"
]

for phone in phone_cases:
    result = contact_cleaner.clean_phone_number(phone, "UA")
    # All result in E.164 format: "+380441234567"
```

#### Scenario: Email Address Cleaning
```python
# Clean and standardize email addresses
email_cases = [
    "  john.doe@example.com  ",
    "john.doe [at] example.com",
    "JOHN.DOE@EXAMPLE.COM",
    "john.doe@example.com.uk"
]

for email in email_cases:
    cleaned = contact_cleaner.clean_email_address(email)
    # Result: "john.doe@example.com" (lowercase, normalized)
```

#### Scenario: Contact Name Parsing and Cleaning
```python
# Clean and parse contact names
name_cases = [
    "  John Doe  ",
    "Dr. John A. Doe",
    "Doe, John",
    "John Michael Doe Jr."
]

for name in name_cases:
    parsed = contact_cleaner.clean_contact_name(name)
    # Result: Structured name components
```

### REQ-DOMAIN-CLEAN-004: Product and Entity Cleaners

#### Description
The system MUST provide specialized cleaners for product data that handle names, descriptions, weights, and categories.

#### Scenario: Product Name and Description Cleaning
```python
from udns.cleaners import ProductCleaner

product_cleaner = ProductCleaner()

# Clean product information
product_data = {
    "name": "  Arabica Coffee Beans 1kg  ",
    "description": "Premium quality arabica coffee beans...  ",
    "weight": "1 KG",
    "category": "Food & Beverages > Coffee"
}

cleaned = product_cleaner.clean_product_data(product_data)
# Result: Properly formatted product information
```

#### Scenario: Weight and Measurement Standardization
```python
# Standardize weights and measurements
weight_cases = [
    "1kg",
    "1 KG",
    "1.0 kg",
    "1000g",
    "2.2 lbs"
]

for weight in weight_cases:
    standardized = product_cleaner.clean_weight(weight, "kg")
    # Result: Numeric value with standardized unit
```

#### Scenario: Category Path Cleaning
```python
# Clean and standardize category hierarchies
category_cases = [
    "Food & Beverages > Coffee > Beans",
    "Food/Beverages/Coffee/Beans",
    "Food and Beverages / Coffee / Beans"
]

for category in category_cases:
    cleaned = product_cleaner.clean_category_path(category)
    # Result: Standardized array format
```

## MODIFIED Requirements

### REQ-DOMAIN-CLEAN-MOD-001: Enhanced Entity Type Detection with Cleaning Context

#### Description
The existing entity type detection system MUST be enhanced to consider cleaning context and data quality indicators.

#### Scenario: Context-Aware Entity Detection
```python
from udns import UDNSProcessor

processor = UDNSProcessor()

# Input with cleaning context
input_text = "  Invoice #A-1027 from   GLOBEX CORP. Total: $2,345.67  "

# Enhanced detection considers cleaning patterns
entity_type = processor.detect_entity_type_with_cleaning(input_text)
# Returns enhanced detection with confidence scores
```

#### Scenario: Cleaning-Aware Processing
```python
# Processing with cleaning context
result = processor.process_with_cleaning_context(
    input_text,
    cleaning_hints={"remove_extra_spaces": True, "standardize_case": True}
)
```

## REMOVED Requirements

*(No requirements removed in this delta)*