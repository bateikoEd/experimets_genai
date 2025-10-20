#!/usr/bin/env python3
"""
UDNS Demo Script - Demonstrates the Universal Data Normalization Specification implementation.
"""

import json
from udns import UDNSProcessor, EntityType


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_result(input_text: str, result_dict: dict):
    """Print formatted processing result."""
    print(f"\n📝 Input:")
    print(f"   {input_text}")
    
    print(f"\n✅ Output:")
    print(f"   Entity Type: {result_dict['entity_type']}")
    print(f"   Confidence: {result_dict['metadata']['confidence']:.2f}")
    
    print(f"\n📊 Attributes:")
    for key, value in result_dict['attributes'].items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     {sub_key}: {sub_value}")
        elif isinstance(value, list):
            print(f"   {key}: {json.dumps(value)}")
        else:
            print(f"   {key}: {value}")


def demo_individual_parsing():
    """Demonstrate parsing of individual entity types."""
    print_section("Individual Entity Type Parsing")
    
    processor = UDNSProcessor(enable_validation=False)
    
    examples = [
        ("Invoice", "Invoice #A-1027 | Vendor: Globex Ltd. | Date: 03/09/2025 | Total: £2,345.70 (VAT 20%)", EntityType.INVOICE),
        ("Address", "Bill To: Nguyen Thi Lan, 12/5 Tran Hung Dao, Dist. 1, Ho Chi Minh City 700000, Vietnam", EntityType.ADDRESS),
        ("Contact", "Support: (044) 123-45-67 ext 123, help[at]example.ua", EntityType.CONTACT),
        ("Product", "Name: Arabica Coffee Beans 1kg — Price: €19,90 — Category: Grocery > Coffee & Tea", EntityType.PRODUCT),
        ("Person", "Prof. François L'Écuyer (CTO) — francois.lecuyer@example.fr — +33 (0)1 23 45 67 89", EntityType.PERSON),
    ]
    
    for name, text, entity_type in examples:
        print(f"\n🔍 Processing {name}:")
        try:
            result = processor.process(text, entity_type)
            print_result(text, result.to_dict())
        except Exception as e:
            print(f"❌ Error: {e}")


def demo_auto_detection():
    """Demonstrate automatic entity type detection."""
    print_section("Automatic Entity Type Detection")
    
    processor = UDNSProcessor(enable_validation=False)
    
    test_inputs = [
        "Invoice #12345 from ACME Corp - Total: $1,250.00",
        "Contact me at john@example.com or call +1-555-0123",
        "Prof. Smith (Director) - smith@university.edu",
        "Coffee Beans Premium 500g - Price: $24.99",
        "Delivery to: Jane Doe, 456 Oak Street, Springfield 62701, USA",
    ]
    
    for i, text in enumerate(test_inputs, 1):
        print(f"\n🎯 Auto-Detection Example {i}:")
        try:
            # Let UDNS detect entity type automatically
            result = processor.process(text)
            print_result(text, result.to_dict())
        except Exception as e:
            print(f"❌ Error: {e}")


def demo_data_normalization():
    """Demonstrate data type normalization features."""
    print_section("Data Type Normalization Examples")
    
    from udns.normalizers import DataNormalizer
    normalizer = DataNormalizer()
    
    print("\n📅 Date Normalization:")
    dates = ["03/09/2025", "2025-09-03", "03-09-2025"]
    for date_str in dates:
        try:
            result, metadata = normalizer.normalize_date(date_str)
            print(f"   {date_str} → {result} (ISO 8601)")
        except Exception as e:
            print(f"   {date_str} → Error: {e}")
    
    print("\n💰 Currency Normalization:")
    currencies = ["£2,345.70", "€19.90", "$100", "¥5000"]
    for currency_str in currencies:
        try:
            result, metadata = normalizer.normalize_currency(currency_str)
            print(f"   {currency_str} → {result['amount']} {result.get('currency_code', 'N/A')}")
        except Exception as e:
            print(f"   {currency_str} → Error: {e}")
    
    print("\n📧 Email Normalization:")
    emails = ["help[at]example.ua", "user@domain.com", "test.email+tag@example.org"]
    for email_str in emails:
        try:
            result, metadata = normalizer.normalize_email(email_str)
            print(f"   {email_str} → {result}")
            if metadata.get('transformations'):
                print(f"     Transformations: {metadata['transformations']}")
        except Exception as e:
            print(f"   {email_str} → Error: {e}")
    
    print("\n🌍 Country Normalization:")
    countries = ["Vietnam", "GB", "USA", "Ukraine"]
    for country_str in countries:
        try:
            result, metadata = normalizer.normalize_country(country_str)
            print(f"   {country_str} → {result} (ISO 3166-1 alpha-3)")
        except Exception as e:
            print(f"   {country_str} → Error: {e}")


def demo_batch_processing():
    """Demonstrate batch processing capabilities."""
    print_section("Batch Processing")
    
    processor = UDNSProcessor(enable_validation=False)
    
    batch_inputs = [
        {
            'id': 'invoice_001',
            'text': 'Invoice #INV-001 from TechCorp Ltd. | Date: 2025-10-20 | Total: $1,500.00',
            'entity_type': 'invoice'
        },
        {
            'id': 'contact_001',
            'text': 'Technical Support: support@techcorp.com, +1-800-555-0199 ext 42'
        },
        {
            'id': 'person_001',
            'text': 'Dr. Maria Rodriguez (Chief Scientist) - maria.rodriguez@research.org'
        },
        {
            'id': 'product_001',
            'text': 'Wireless Headphones Pro — Price: €299.99 — Category: Electronics > Audio'
        }
    ]
    
    print(f"\n📦 Processing batch of {len(batch_inputs)} inputs:")
    
    results = processor.process_batch(batch_inputs)
    
    for result in results:
        print(f"\n🔸 {result['id']}:")
        if result['success']:
            entity = result['entity']
            print(f"   ✅ Success: {entity['entity_type']} (confidence: {entity['metadata']['confidence']:.2f})")
            print(f"   📊 {len(entity['attributes'])} attributes extracted")
        else:
            print(f"   ❌ Failed: {result['error']}")


def demo_validation_examples():
    """Demonstrate validation against temp.json examples."""
    print_section("Validation Against Examples")
    
    try:
        with open('data/temp.json', 'r') as f:
            test_data = json.load(f)
        
        processor = UDNSProcessor(enable_validation=False)
        
        domain_mapping = {
            'invoices': EntityType.INVOICE,
            'addresses': EntityType.ADDRESS,
            'contacts': EntityType.CONTACT,
            'products': EntityType.PRODUCT,
            'people': EntityType.PERSON,
        }
        
        print(f"\n📋 Testing against {len(test_data['examples'])} examples:")
        
        passed = 0
        total = 0
        
        for example in test_data['examples'][:5]:  # Test first 5 examples
            example_id = example['id']
            domain = example['domain']
            input_text = example['input_text']
            
            entity_type = domain_mapping.get(domain)
            if not entity_type:
                print(f"   {example_id}: SKIP (no parser for {domain})")
                continue
            
            total += 1
            
            try:
                result = processor.process(input_text, entity_type)
                passed += 1
                print(f"   {example_id}: ✅ PASS (confidence: {result.metadata.confidence:.2f})")
            except Exception as e:
                print(f"   {example_id}: ❌ FAIL ({str(e)[:50]}...)")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n📈 Results: {passed}/{total} passed ({success_rate:.1f}%)")
        
    except FileNotFoundError:
        print("\n⚠️  temp.json examples file not found. Skipping validation demo.")
    except Exception as e:
        print(f"\n❌ Error loading examples: {e}")


def main():
    """Main demo function."""
    print("🎯 Universal Data Normalization Specification (UDNS) v1.0")
    print("   Implementation Demo")
    print("   OpenSpec Proposal by Eduard Bateiko")
    
    try:
        demo_individual_parsing()
        demo_auto_detection()
        demo_data_normalization()
        demo_batch_processing()
        demo_validation_examples()
        
        print_section("Demo Complete")
        print("\n🎉 UDNS Demo completed successfully!")
        print("\n📚 Next steps:")
        print("   • Try the CLI: python udns_cli.py --help")
        print("   • Run tests: python test_udns.py")
        print("   • Read the OpenSpec proposal: openspec-proposal.md")
        print("   • Check the README.md for detailed documentation")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Demo error: {e}")


if __name__ == '__main__':
    main()