# Project Context

## Purpose
This project is a Python SDK for data extraction and normalization that converts unstructured text input into standardized, structured data formats. The SDK handles various domain entities (invoices, addresses, contacts, products, orders, log events, calendar events, payments, measurements, and people) and transforms them into a unified output format with consistent attributes and metadata.

### Key Goals
- Provide a unified API for extracting and normalizing data across multiple domains
- Ensure consistent output format with standardized entity types, attributes, and metadata
- Support international standards (ISO 8601 for dates, ISO 4217 for currencies, E.164 for phones)
- Maintain high confidence scoring and traceability through metadata
- Enable extensible domain-specific normalization rules

## Tech Stack
- **Python 3.8+**: Core runtime environment
- **pandas >= 1.5.0**: Data manipulation and analysis
- **numpy >= 1.21.0**: Numerical computations and array operations  
- **matplotlib >= 3.5.0**: Data visualization and plotting
- **seaborn >= 0.11.0**: Statistical data visualization
- **scipy >= 1.9.0**: Scientific computing and statistical functions
- **plotly >= 5.0.0**: Interactive visualizations
- **pytest**: Testing framework (per project requirements)
- **jupyter**: Notebook support for development and documentation

## Project Conventions

### Code Style
- **PEP 8**: Follow Python Enhancement Proposal 8 style guidelines
- **Type Hints**: Use type annotations for all public APIs and complex functions
- **Docstrings**: Google-style docstrings for all public classes and methods
- **Naming Conventions**:
  - Classes: `PascalCase` (e.g., `DataNormalizer`, `EntityExtractor`)
  - Functions/methods: `snake_case` (e.g., `extract_data`, `normalize_output`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_CONFIDENCE_THRESHOLD`)
  - Private methods: `_snake_case` (e.g., `_parse_internal`)

### Architecture Patterns
- **Plugin Architecture**: Domain-specific extractors as pluggable components
- **Strategy Pattern**: Interchangeable normalization strategies per entity type
- **Factory Pattern**: Entity extractor factory for domain selection
- **Pipeline Pattern**: Sequential processing stages (extract → normalize → validate)
- **Dependency Injection**: Configuration and rule injection for extensibility

### Testing Strategy
- **pytest**: Primary testing framework
- **Unit Tests**: Test individual extractor and normalizer components
- **Integration Tests**: Test end-to-end data transformation pipelines  
- **Fixture-based Testing**: Use `data_examples.json` as test fixtures
- **Property-based Testing**: Validate output schema compliance
- **Coverage Requirements**: Minimum 90% code coverage for core modules
- **Test Structure**:
  ```
  tests/
  ├── unit/
  │   ├── test_extractors/
  │   ├── test_normalizers/
  │   └── test_validators/
  ├── integration/
  │   └── test_pipelines/
  └── fixtures/
      └── data_examples.json
  ```

### Git Workflow
- **Feature Branches**: `feature/description` for new capabilities
- **Bugfix Branches**: `bugfix/issue-description` for fixes
- **Main Branch**: `main` (protected, requires PR approval)
- **Commit Messages**: Conventional commits format (feat:, fix:, docs:, test:)
- **PR Requirements**: All tests pass, code review approval, OpenSpec compliance

## Domain Context

### Supported Entity Types
The SDK handles 10 primary entity types with specific normalization rules:

1. **Invoices**: Financial documents with vendor, dates, amounts, tax information
2. **Addresses**: Physical addresses with international formatting standards
3. **Contacts**: Phone numbers (E.164) and email addresses  
4. **Products**: Items with names, prices, categories, specifications
5. **Orders**: Purchase orders with line items and shipping information
6. **Log Events**: System logs with timestamps, levels, and structured data
7. **Calendar Events**: Scheduled events with timezone-aware timestamps
8. **Payments**: Financial transactions with amounts, currencies, methods
9. **Measurements**: Physical specifications with unit conversions
10. **People**: Person entities with names, roles, contact information

### Normalization Standards
- **Dates**: ISO 8601 format (`YYYY-MM-DDTHH:mm:ssZ`)
- **Currency**: ISO 4217 codes (USD, EUR, GBP, etc.)
- **Phone Numbers**: E.164 international format (`+[country][number]`)
- **Decimal Numbers**: Dot notation with appropriate precision
- **Country Codes**: ISO 3166-1 alpha-3 (USA, GBR, DEU, etc.)

### Output Schema
All normalized outputs follow the unified wrapper format:
```json
{
  "entity_type": "string",
  "attributes": { /* domain-specific fields */ },
  "metadata": {
    "confidence": "float[0.0-1.0]",
    /* additional processing metadata */
  }
}
```

## Important Constraints

### Data Quality
- **Confidence Scoring**: All extractions must include confidence scores (0.0-1.0)
- **Metadata Preservation**: Track transformation steps and rule applications
- **Input Validation**: Graceful handling of malformed or incomplete input
- **Locale Awareness**: Support for international data formats and conventions

### Performance
- **Memory Efficiency**: Handle large document processing without excessive memory usage
- **Processing Speed**: Sub-second response times for typical text inputs
- **Scalability**: Designed for batch processing of multiple documents

### Standards Compliance  
- **International Standards**: Strict adherence to ISO standards for dates, currencies, countries
- **Unicode Support**: Full UTF-8 support for international text
- **Accessibility**: Clear error messages and validation feedback

## External Dependencies

### Core Libraries
- **pandas/numpy**: Essential for data manipulation and numerical operations
- **Standard Library**: Heavy reliance on `json`, `datetime`, `re`, `collections`
- **pytest**: Testing infrastructure and assertion libraries

### Optional Integrations
- **Jupyter Ecosystem**: Development and documentation notebooks
- **Visualization**: matplotlib, seaborn, plotly for data analysis
- **Locale Support**: System locale libraries for international formatting

### Development Tools
- **Version Control**: Git with GitHub integration
- **CI/CD**: GitHub Actions (configured in `.github/`)
- **Environment Management**: Virtual environments (`.venv/`)
- **OpenSpec**: Specification and change management system
