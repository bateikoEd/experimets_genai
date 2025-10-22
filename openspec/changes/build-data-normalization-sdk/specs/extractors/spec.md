## ADDED Requirements

### Requirement: Domain Extractor Framework
The system SHALL provide a base framework for domain-specific extractors with consistent interfaces and automatic discovery mechanisms.

#### Scenario: Base Extractor Interface
- **WHEN** a developer creates a new domain extractor
- **THEN** they inherit from `BaseExtractor` with standardized methods
- **AND** the extractor implements `extract(text: str) -> Dict[str, Any]` method
- **AND** the extractor defines supported entity types and confidence calculation rules

#### Scenario: Extractor Registration and Discovery
- **WHEN** the SDK initializes
- **THEN** it automatically discovers all available extractor classes
- **AND** registers extractors by their supported entity types
- **AND** handles conflicts when multiple extractors support the same entity type

### Requirement: Invoice Data Extraction
The system SHALL extract structured invoice data including vendor information, dates, amounts, and tax details from unstructured text.

#### Scenario: Basic Invoice Parsing
- **WHEN** processing invoice text like "Invoice #A-1027 | Vendor: Globex Ltd. | Date: 03/09/2025 | Total: £2,345.70 (VAT 20%)"
- **THEN** the extractor identifies invoice_number as "A-1027"
- **AND** extracts vendor_name as "Globex Ltd."
- **AND** parses invoice_date as raw date string "03/09/2025"
- **AND** extracts total_amount as raw value "£2,345.70" with currency symbol
- **AND** identifies tax_rate_percent as "20%" from VAT information

#### Scenario: Invoice Pattern Recognition
- **WHEN** text contains invoice-specific keywords and patterns
- **THEN** the extractor achieves high confidence (>0.9) for clear invoice formats
- **AND** provides medium confidence (0.6-0.9) for partial invoice information
- **AND** returns low confidence (<0.6) when invoice patterns are ambiguous

### Requirement: Address Data Extraction
The system SHALL extract structured address components including person names, street addresses, districts, cities, and countries from various international formats.

#### Scenario: International Address Parsing
- **WHEN** processing address text like "Bill To: Nguyen Thi Lan, 12/5 Tran Hung Dao, Dist. 1, Ho Chi Minh City 700000, Vietnam"
- **THEN** the extractor identifies person components (given, middle, family names)
- **AND** extracts street_address as "12/5 Tran Hung Dao"
- **AND** parses district as "Dist. 1" with normalization hints
- **AND** identifies city as "Ho Chi Minh City"
- **AND** extracts postal_code as "700000"
- **AND** identifies country as "Vietnam" with confidence indicators

#### Scenario: Address Format Variability
- **WHEN** addresses use different cultural formatting conventions
- **THEN** the extractor adapts to common international formats
- **AND** handles various postal code formats and positions
- **AND** recognizes country-specific address components and terminology

### Requirement: Contact Information Extraction
The system SHALL extract contact details including phone numbers, emails, and extensions from various formatting styles.

#### Scenario: Phone and Email Extraction
- **WHEN** processing contact text like "Support: (044) 123-45-67 ext 123, help[at]example.ua"
- **THEN** the extractor identifies phone number "(044) 123-45-67"
- **AND** extracts extension "123" separately from main number
- **AND** parses email "help[at]example.ua" with format transformation hints
- **AND** infers country context from area code patterns when possible

#### Scenario: Contact Format Recognition
- **WHEN** contact information uses obfuscation or alternative formatting
- **THEN** the extractor recognizes patterns like "[at]" for "@" symbols
- **AND** handles various phone number formatting conventions
- **AND** maintains confidence scoring based on format certainty

### Requirement: Product Information Extraction
The system SHALL extract product data including names, specifications, prices, and category information from product descriptions.

#### Scenario: Product Detail Parsing
- **WHEN** processing product text like "Name: Arabica Coffee Beans 1kg — Price: €19,90 — Category: Grocery > Coffee & Tea"
- **THEN** the extractor identifies product name "Arabica Coffee Beans"
- **AND** extracts weight specification "1kg" with unit information
- **AND** parses price "€19,90" with currency and decimal format
- **AND** extracts hierarchical category path ["Grocery", "Coffee & Tea"]

#### Scenario: Product Specification Parsing
- **WHEN** products include technical specifications or variants
- **THEN** the extractor separates core names from specifications
- **AND** identifies measurable attributes (weight, size, volume)
- **AND** preserves specification details for normalization processing

### Requirement: Order Data Extraction
The system SHALL extract order information including line items, quantities, SKUs, and shipping details from order text.

#### Scenario: Order Line Item Parsing
- **WHEN** processing order text like "Items: 2 x SKU-1001 (Blue T-Shirt M), 1x SKU-2020 (Jeans 32/32); Ship by: 2025-10-22"
- **THEN** the extractor identifies multiple line items as separate entries
- **AND** extracts quantities (2, 1) with associated products
- **AND** parses SKUs ("SKU-1001", "SKU-2020") as product identifiers
- **AND** extracts product names and variants from parenthetical descriptions
- **AND** identifies shipping dates with temporal parsing hints

#### Scenario: Order Format Flexibility
- **WHEN** orders use various quantity and item formatting conventions
- **THEN** the extractor handles different multiplier symbols (x, ×, *)
- **AND** processes comma and semicolon separators between items
- **AND** recognizes parenthetical information as variants or specifications

### Requirement: Log Event Extraction
The system SHALL extract structured log data including levels, timestamps, components, and message details from log entries.

#### Scenario: Structured Log Parsing
- **WHEN** processing log text like "WARN [Payments] 2025/09/17 08:45:10 UTC user=984 ip=10.0.1.5 msg='Retryable timeout'"
- **THEN** the extractor identifies log level "WARN"
- **AND** extracts component "[Payments]" with bracketing recognition
- **AND** parses timestamp "2025/09/17 08:45:10 UTC" with timezone information
- **AND** extracts key-value pairs (user=984, ip=10.0.1.5)
- **AND** identifies message content "Retryable timeout" from quoted strings

#### Scenario: Log Format Variations
- **WHEN** logs use different timestamp formats and structured data patterns
- **THEN** the extractor adapts to common logging frameworks and formats
- **AND** handles various log level naming conventions
- **AND** recognizes different key-value pair separators and quote styles

### Requirement: Calendar Event Extraction
The system SHALL extract event information including titles, dates, times, durations, and timezone data from event descriptions.

#### Scenario: Event Detail Parsing
- **WHEN** processing event text like "Standup — 20 Oct 2025, 09:30–09:50 Europe/Kyiv"
- **THEN** the extractor identifies event title "Standup"
- **AND** parses start date and time "20 Oct 2025, 09:30"
- **AND** extracts end time "09:50" from time range notation
- **AND** identifies timezone "Europe/Kyiv" as IANA timezone reference
- **AND** calculates duration from start and end times

#### Scenario: Event Format Recognition
- **WHEN** events use various date formats and time range notations
- **THEN** the extractor handles different date representation styles
- **AND** recognizes various time range separators (–, -, to, until)
- **AND** processes timezone abbreviations and full IANA names

### Requirement: Payment Information Extraction
The system SHALL extract payment data including amounts, currencies, methods, authorization codes, and timestamps from payment descriptions.

#### Scenario: Payment Detail Parsing
- **WHEN** processing payment text like "Paid: 5,000 JPY via card on 2025-08-01 14:22 JST (Auth: 9ZK12)."
- **THEN** the extractor identifies payment amount "5,000" with number formatting
- **AND** extracts currency "JPY" as currency code
- **AND** identifies payment method "card" from method keywords
- **AND** parses payment timestamp "2025-08-01 14:22 JST"
- **AND** extracts authorization code "9ZK12" from parenthetical information

#### Scenario: Payment Method Recognition
- **WHEN** payments reference various payment methods and formats
- **THEN** the extractor recognizes common payment method terms
- **AND** handles different currency amount formatting conventions
- **AND** identifies authorization and transaction codes reliably

### Requirement: Measurement Data Extraction
The system SHALL extract physical measurements including dimensions, weights, and units from specification text.

#### Scenario: Dimension and Weight Parsing
- **WHEN** processing measurement text like "Spec: 10 in × 6 in × 2.5 in; weight 1 lb 4 oz"
- **THEN** the extractor identifies three-dimensional measurements
- **AND** extracts individual dimension values (10, 6, 2.5) with units
- **AND** recognizes dimension separators (×, x, by)
- **AND** parses compound weight "1 lb 4 oz" as separate quantity and unit pairs
- **AND** preserves unit information for conversion processing

#### Scenario: Unit Format Recognition
- **WHEN** measurements use various unit abbreviations and formatting styles
- **THEN** the extractor handles common imperial and metric unit abbreviations
- **AND** recognizes compound units (feet and inches, pounds and ounces)
- **AND** maintains precision information from decimal specifications

### Requirement: People Information Extraction
The system SHALL extract person data including names, titles, roles, and contact information from person descriptions.

#### Scenario: Person Detail Parsing
- **WHEN** processing person text like "Prof. François L'Écuyer (CTO) — francois.lecuyer@example.fr — +33 (0)1 23 45 67 89"
- **THEN** the extractor identifies honorific "Prof." as title prefix
- **AND** parses full name "François L'Écuyer" with special characters
- **AND** extracts role "(CTO)" from parenthetical position information
- **AND** identifies email address with domain information
- **AND** parses international phone number with country and formatting codes

#### Scenario: Name and Title Recognition
- **WHEN** person information includes various cultural naming patterns and professional titles
- **THEN** the extractor handles international character sets and accents
- **AND** recognizes common honorifics and professional designations
- **AND** processes different name ordering conventions (given/family name variations)