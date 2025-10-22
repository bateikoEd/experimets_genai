# Build Data Normalization SDK

## Why

This project currently lacks the core Python SDK implementation needed to extract and normalize unstructured text data into standardized formats. The existing `data/data_examples.json` demonstrates 10 diverse entity types (invoices, addresses, contacts, products, orders, log events, calendar events, payments, measurements, and people) that require consistent processing through a unified API. Without this SDK, users cannot programmatically transform raw text into structured, standardized data that complies with international standards (ISO 8601 for dates, ISO 4217 for currencies, E.164 for phones).

## What Changes

- **NEW**: Complete Python SDK with modular architecture supporting pluggable extractors and normalizers
- **NEW**: Core framework with unified output schema and confidence scoring
- **NEW**: Domain-specific extractors for 10 entity types with pattern recognition and text parsing
- **NEW**: Normalizers implementing international standards (ISO 8601, ISO 4217, E.164, etc.)
- **NEW**: Validation system with confidence thresholds and metadata tracking
- **NEW**: Comprehensive test suite using pytest with fixtures from `data_examples.json`
- **NEW**: Package structure with proper `setup.py`/`pyproject.toml` configuration
- **NEW**: Documentation and usage examples

## Impact

- **Affected specs**: This creates 4 new capability specs:
  - `core`: Framework, configuration, and unified API
  - `extractors`: Domain-specific text extraction and pattern matching
  - `normalizers`: Standards-compliant data transformation
  - `validators`: Output validation and confidence scoring

- **Affected code**: Creates entire new codebase:
  - `src/data_normalization_sdk/`: Main package directory
  - `tests/`: pytest-based test suite
  - `pyproject.toml`: Package configuration
  - `README.md`: Updated with SDK usage
  - `examples/`: Usage demonstrations

- **Dependencies**: Leverages existing `requirements.txt` with pandas, numpy, and testing tools

- **Deliverable**: Production-ready Python SDK that users can install and use immediately for data extraction and normalization tasks