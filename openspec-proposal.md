# Universal Data Normalization Specification (UDNS) v1.0
## OpenSpec Proposal

### Abstract

This specification defines a universal format for normalizing unstructured text data across multiple domains into a consistent, machine-readable structure. The Universal Data Normalization Specification (UDNS) provides a standardized approach to extract, transform, and represent data from various sources while preserving semantic meaning and maintaining interoperability.

### 1. Introduction

#### 1.1 Purpose
The purpose of this specification is to establish a common framework for data normalization that can be applied across different domains such as invoices, addresses, contacts, products, orders, log events, calendar events, payments, measurements, and personal information.

#### 1.2 Scope
This specification covers:
- Universal wrapper format for normalized data
- Standard attribute naming conventions
- Metadata requirements and conventions
- Domain-specific normalization rules
- Data type representations and standards
- Project structure and organization guidelines

#### 1.3 Conformance
Implementations that claim conformance to this specification MUST implement all required features and SHOULD implement optional features where applicable.

### 2. Data Structure

#### 2.1 Universal Wrapper Format

All normalized output MUST conform to the following structure:

```json
{
  "entity_type": "string",
  "attributes": {
    // Domain-specific normalized data
  },
  "metadata": {
    // Processing and confidence information
  }
}
```

#### 2.2 Required Fields

##### 2.2.1 entity_type
- **Type**: String
- **Required**: Yes
- **Description**: Specifies the type of entity being normalized
- **Valid Values**: `invoice`, `address`, `contact`, `product`, `order`, `log_event`, `event`, `payment`, `spec`, `person`
- **Extensibility**: Additional entity types MAY be defined for domain-specific use cases

##### 2.2.2 attributes
- **Type**: Object
- **Required**: Yes
- **Description**: Contains the normalized data specific to the entity type
- **Constraints**: Field names MUST use snake_case convention

##### 2.2.3 metadata
- **Type**: Object
- **Required**: Yes
- **Description**: Contains processing information, confidence scores, and transformation details

### 3. Standard Data Types and Formats

#### 3.1 Date and Time
- **Standard**: ISO 8601
- **Format**: `YYYY-MM-DDTHH:mm:ssZ` or `YYYY-MM-DDTHH:mm:ss±HH:mm`
- **Date Only**: `YYYY-MM-DD`

#### 3.2 Currency
- **Standard**: ISO 4217
- **Format**: Three-letter currency codes (e.g., `USD`, `EUR`, `GBP`)
- **Amount**: Decimal numbers with dot as decimal separator

#### 3.3 Phone Numbers
- **Standard**: E.164
- **Format**: `+[country code][number]` (e.g., `+380441234567`)

#### 3.4 Country Codes
- **Standard**: ISO 3166-1 alpha-3
- **Format**: Three-letter country codes (e.g., `USA`, `GBR`, `UKR`)

#### 3.5 Numbers
- **Format**: Decimal notation with dot as decimal separator
- **Scientific Notation**: Acceptable for very large or small numbers

### 4. Metadata Requirements

#### 4.1 Required Metadata Fields

##### 4.1.1 confidence
- **Type**: Number (0.0 - 1.0)
- **Required**: Yes
- **Description**: Confidence score of the normalization process

#### 4.2 Optional Metadata Fields

##### 4.2.1 Processing Information
- `parser_version`: Version of the parser used
- `source`: Source of the input data (e.g., `ocr`, `user_input`, `api`)
- `locale_hint` / `locale_detected`: Detected or suggested locale
- `transformations`: Array of transformations applied

##### 4.2.2 Standards and Rules
- `standard`: Applied standard (e.g., `E.164`, `ISO 8601`)
- `normalization_ruleset`: Ruleset used for normalization
- `schema`: Schema format applied

### 5. Domain-Specific Schemas

#### 5.1 Invoice Schema
```json
{
  "entity_type": "invoice",
  "attributes": {
    "invoice_number": "string",
    "vendor_name": "string",
    "invoice_date": "ISO 8601 date",
    "total_amount": "number",
    "currency_code": "ISO 4217",
    "tax_rate_percent": "number (optional)"
  }
}
```

#### 5.2 Address Schema
```json
{
  "entity_type": "address",
  "attributes": {
    "person": {
      "given_name": "string",
      "middle_name": "string (optional)",
      "family_name": "string"
    },
    "street_address": "string",
    "district": "string (optional)",
    "city": "string",
    "postal_code": "string",
    "region": "string (optional)",
    "country_name": "string",
    "country_code": "ISO 3166-1 alpha-3"
  }
}
```

#### 5.3 Contact Schema
```json
{
  "entity_type": "contact",
  "attributes": {
    "phone_e164": "E.164 format (optional)",
    "phone_extension": "string (optional)",
    "email": "string (optional)",
    "country_code_inferred": "ISO 3166-1 alpha-3 (optional)"
  }
}
```

#### 5.4 Product Schema
```json
{
  "entity_type": "product",
  "attributes": {
    "name": "string",
    "net_weight_kg": "number (optional)",
    "price": "number (optional)",
    "currency_code": "ISO 4217 (optional)",
    "category_path": "array of strings (optional)"
  }
}
```

#### 5.5 Order Schema
```json
{
  "entity_type": "order",
  "attributes": {
    "lines": [
      {
        "sku": "string",
        "name": "string",
        "variant": "string (optional)",
        "quantity": "number"
      }
    ],
    "requested_ship_date": "ISO 8601 date (optional)"
  }
}
```

### 6. Processing Guidelines

#### 6.1 Text Normalization
- Remove unnecessary punctuation while preserving semantic meaning
- Standardize whitespace and formatting
- Convert to appropriate character encoding (UTF-8)

#### 6.2 Locale Handling
- Detect locale when possible and include in metadata
- Apply locale-specific formatting rules
- Support multiple locale formats for the same data type

#### 6.3 Error Handling
- Include confidence scores for all extractions
- Document failed extractions in metadata
- Provide fallback values when appropriate

#### 6.4 Extensibility
- Allow custom entity types for domain-specific use cases
- Support additional attributes beyond core schema
- Maintain backward compatibility when extending schemas

### 7. Validation

#### 7.1 Schema Validation
Implementations SHOULD validate normalized output against the defined schemas for each entity type.

#### 7.2 Data Type Validation
All data types MUST conform to their specified standards (ISO 8601, E.164, etc.).

#### 7.3 Confidence Thresholds
Implementations MAY define minimum confidence thresholds for accepting normalized data.

### 8. Project Structure

#### 8.1 Standard Project Organization

Implementations SHOULD follow the standard project structure for consistency and maintainability:

```
project-root/
├── src/
│   └── your_sdk/
│       ├── __init__.py
│       ├── client.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── endpoints.py
│       │   └── utils.py
│       ├── auth/
│       │   ├── __init__.py
│       │   └── token_manager.py
│       └── exceptions.py
├── tests/
│   ├── __init__.py
│   └── test_client.py
├── examples/
│   └── quickstart.py
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
└── .env.example
```

#### 8.2 Directory Structure Guidelines

##### 8.2.1 Source Code (`src/your_sdk/`)
- **`__init__.py`**: Package initialization and main exports
- **`client.py`**: Main client class for API interactions
- **`api/`**: API-related modules
  - **`models.py`**: Data models and schemas
  - **`endpoints.py`**: API endpoint definitions
  - **`utils.py`**: Utility functions for API operations
- **`auth/`**: Authentication and authorization modules
  - **`token_manager.py`**: Token management and refresh logic
- **`exceptions.py`**: Custom exception classes

##### 8.2.2 Tests (`tests/`)
- **`__init__.py`**: Test package initialization
- **`test_client.py`**: Main client tests
- Additional test files SHOULD be organized by functionality

##### 8.2.3 Examples (`examples/`)
- **`quickstart.py`**: Quick start guide and basic usage examples
- Additional examples SHOULD demonstrate specific use cases

##### 8.2.4 Configuration Files
- **`pyproject.toml`**: Project configuration and dependencies
- **`README.md`**: Project documentation
- **`LICENSE`**: License file
- **`.gitignore`**: Git ignore rules
- **`.env.example`**: Environment variable template

#### 8.3 Implementation Requirements

##### 8.3.1 Package Structure
- All code MUST be contained within the `src/your_sdk/` directory
- Package imports SHOULD use relative imports within the package
- Public APIs MUST be exposed through `__init__.py`

##### 8.3.2 Testing Structure
- Tests MUST be located in the `tests/` directory
- Test files SHOULD mirror the source code structure
- Test coverage SHOULD include all public APIs and critical paths

##### 8.3.3 Documentation
- Examples MUST be provided in the `examples/` directory
- README.md MUST include installation, usage, and contribution guidelines
- API documentation SHOULD be generated from docstrings

### 9. Security Considerations

#### 9.1 Data Privacy
- Ensure compliance with data protection regulations
- Implement appropriate data anonymization when required
- Secure handling of personally identifiable information (PII)

#### 9.2 Input Sanitization
- Validate and sanitize all input data
- Prevent injection attacks through malformed input
- Implement rate limiting for processing requests

### 9. Examples

See the accompanying `temp.json` file for comprehensive examples of each entity type and their normalized representations.

### 10. Versioning

This specification follows semantic versioning (SemVer):
- **Major**: Breaking changes to core structure
- **Minor**: Addition of new entity types or optional fields
- **Patch**: Bug fixes and clarifications

Current Version: **1.0.0**

### 11. References

- ISO 8601: Date and time format
- ISO 4217: Currency codes
- E.164: International telephone numbering plan
- ISO 3166-1: Country codes
- RFC 5322: Internet Message Format (for email validation)
- Unicode Standard: Character encoding and normalization

### 12. Conformance Statement

This specification defines requirements using the key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" as described in RFC 2119.

---

**Document Status**: Proposal  
**Version**: 1.0.0  
**Date**: October 20, 2025  
**Authors**: Eduard Bateiko  
**Contact**: [Contact Information]