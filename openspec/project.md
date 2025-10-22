# Project Context

## Purpose
Universal Data Normalization Specification (UDNS) v1.0 - A comprehensive Python implementation that provides standardized parsing and normalization of unstructured text data across multiple domains. The project aims to establish a common framework for data normalization that can be applied to invoices, addresses, contacts, products, orders, log events, calendar events, payments, measurements, and personal information while preserving semantic meaning and maintaining interoperability.

## Tech Stack
- **Language**: Python 3.8+
- **Core Dependencies**:
  - `jsonschema>=4.0.0` - JSON schema validation
  - `phonenumbers>=8.13.0` - Phone number parsing and validation
- **Development Tools**:
  - `pytest>=7.0.0` - Testing framework
  - `pytest-cov>=4.0.0` - Coverage reporting
  - `black>=22.0.0` - Code formatting
  - `flake8>=5.0.0` - Linting
  - `mypy>=1.0.0` - Type checking
- **Package Management**: setuptools with pyproject.toml support
- **CLI**: Entry point via setuptools console_scripts

## Project Conventions

### Code Style
- **Formatting**: Black code formatter with line length 88 characters
- **Naming**: snake_case for all variables, functions, and methods
- **Classes**: PascalCase for class names
- **Constants**: UPPER_CASE for constants and enum values
- **Imports**: Grouped as: standard library, third-party, local imports
- **Docstrings**: Google-style docstrings for all public APIs
- **Type Hints**: Comprehensive type hints using Python typing module
- **Linting**: flake8 with E501 line length disabled (handled by black)

### Architecture Patterns
- **Modular Design**: Separation of concerns with dedicated modules for core, normalizers, parsers, validators, and processor
- **Strategy Pattern**: Domain-specific parsers implementing common interface
- **Factory Pattern**: Entity type detection and parser selection
- **Data Classes**: Using Python dataclasses for structured data representation
- **Enum Types**: EntityType enum for entity type definitions
- **JSON Schema**: Schema-based validation for all entity types
- **Metadata Pattern**: Rich metadata tracking for confidence scores and transformations

### Testing Strategy
- **Unit Tests**: Comprehensive test coverage for all modules
- **Integration Tests**: End-to-end testing with real-world examples
- **Example Validation**: Validation against temp.json examples
- **Test Coverage**: Target 80%+ coverage with pytest-cov
- **Test Organization**: Mirror source code structure in tests/
- **CLI Testing**: Command-line interface functionality testing
- **Batch Processing**: Test bulk operations and error handling

### Git Workflow
- **Branching**: Feature branches from main with descriptive names
- **Commits**: Conventional commits format (feat:, fix:, docs:, test:, chore:)
- **Pull Requests**: Code review required before merge
- **Versioning**: Semantic versioning (SemVer) with automated changelog
- **Tags**: Git tags for releases following v1.0.0 format

## Domain Context
UDNS operates in the data normalization and text processing domain with specific expertise in:
- **Invoice Processing**: Extracting vendor, amounts, dates, and tax information
- **Address Parsing**: Normalizing postal addresses with international support
- **Contact Information**: Phone number validation (E.164) and email normalization
- **Product Data**: Weight, price, and category extraction
- **Personal Information**: Name parsing with honorifics and roles
- **Multi-language Support**: Unicode normalization and international character handling
- **Standards Compliance**: ISO 8601, ISO 4217, E.164, ISO 3166-1, RFC 5322

## Important Constraints
- **Python Version**: Must support Python 3.8+ for broader compatibility
- **Memory Efficiency**: Low memory footprint for batch processing
- **Performance**: Sub-5ms processing time for typical inputs
- **Standards Adherence**: Strict compliance with international standards
- **Extensibility**: Easy addition of new entity types without breaking changes
- **Validation**: JSON schema validation for all outputs
- **Error Handling**: Graceful degradation with confidence scoring

## External Dependencies
- **jsonschema**: JSON schema validation library
- **phonenumbers**: Google's phone number parsing library
- **pytest**: Testing framework
- **Development Tools**: Black, flake8, mypy for code quality
- **Standards Libraries**: Built-in datetime, re, unicodedata for core functionality
- **CLI Dependencies**: argparse for command-line interface
