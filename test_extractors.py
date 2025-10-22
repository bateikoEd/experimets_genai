#!/usr/bin/env python3
"""
CLI script to test data normalization SDK extractors.

This script allows interactive testing of individual extractors or the full SDK pipeline.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from data_normalization_sdk.core.sdk import DataNormalizationSDK
from data_normalization_sdk.extractors.invoice import InvoiceExtractor
from data_normalization_sdk.extractors.address import AddressExtractor
from data_normalization_sdk.extractors.contact import ContactExtractor
from data_normalization_sdk.extractors.product import ProductExtractor
from data_normalization_sdk.extractors.order import OrderExtractor
from data_normalization_sdk.extractors.log_event import LogEventExtractor
from data_normalization_sdk.extractors.calendar_event import CalendarEventExtractor
from data_normalization_sdk.extractors.payment import PaymentExtractor
from data_normalization_sdk.extractors.measurement import MeasurementExtractor
from data_normalization_sdk.extractors.people import PeopleExtractor


def test_individual_extractor(extractor_name: str, text: str) -> None:
    """Test a specific extractor directly."""
    extractors = {
        'invoice': InvoiceExtractor({}),
        'address': AddressExtractor({}),
        'contact': ContactExtractor({}),
        'product': ProductExtractor({}),
        'order': OrderExtractor({}),
        'log_event': LogEventExtractor({}),
        'calendar_event': CalendarEventExtractor({}),
        'payment': PaymentExtractor({}),
        'measurement': MeasurementExtractor({}),
        'people': PeopleExtractor({})
    }
    
    if extractor_name not in extractors:
        print(f"❌ Unknown extractor: {extractor_name}")
        print(f"Available extractors: {', '.join(extractors.keys())}")
        return
    
    extractor = extractors[extractor_name]
    
    print(f"\n🔍 Testing {extractor_name} extractor")
    print(f"📝 Input: {text}")
    print(f"🎯 Supported types: {extractor.supported_entity_types}")
    
    try:
        data, confidence = extractor.extract(text)
        
        if data:
            print(f"✅ Success! Confidence: {confidence:.3f}")
            print(f"📊 Extracted data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ No data extracted (confidence: {confidence:.3f})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_full_pipeline(text: str) -> None:
    """Test the full SDK pipeline."""
    print(f"\n🚀 Testing full SDK pipeline")
    print(f"📝 Input: {text}")
    
    try:
        sdk = DataNormalizationSDK()
        result = sdk.process(text)
        
        if result:
            print(f"✅ Success!")
            print(f"🏷️  Entity type: {result.entity_type}")
            print(f"📊 Confidence: {result.metadata.confidence:.3f}")
            print(f"🔄 Transformations: {result.metadata.transformations}")
            print(f"📋 Extracted data:")
            print(json.dumps(result.attributes, indent=2, ensure_ascii=False))
        else:
            print(f"❌ No result from SDK pipeline")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_example_data() -> None:
    """Test with example data from data_examples.json."""
    data_file = Path(__file__).parent / "data" / "data_examples.json"
    
    if not data_file.exists():
        print(f"❌ Example data file not found: {data_file}")
        return
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    print(f"\n📚 Testing with example data from {data_file}")
    print(f"Found {len(data['examples'])} examples")
    
    # Filter to implemented extractors
    implemented_domains = {'invoices', 'addresses', 'contacts', 'products', 'orders', 'log_events', 'events_calendar', 'payments', 'measurements', 'people'}
    
    for example in data['examples']:
        if example['domain'] in implemented_domains:
            print(f"\n" + "="*60)
            print(f"🧪 Example {example['id']}: {example['domain']}")
            test_full_pipeline(example['input_text'])
            
            # Show expected output for comparison
            expected = example['normalized_output']
            print(f"\n📋 Expected output:")
            print(f"🏷️  Entity type: {expected['entity_type']}")
            print(f"📊 Confidence: {expected['metadata'].get('confidence', 'N/A')}")
            print(f"📋 Expected attributes:")
            print(json.dumps(expected['attributes'], indent=2, ensure_ascii=False))


def interactive_mode() -> None:
    """Interactive testing mode."""
    print("\n🔧 Interactive Extractor Testing")
    print("Type 'quit' to exit, 'examples' to test with sample data")
    
    while True:
        print("\n" + "-"*50)
        text = input("📝 Enter text to test (or command): ").strip()
        
        if text.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        elif text.lower() == 'examples':
            test_example_data()
            continue
        elif not text:
            continue
        
        # Ask for extractor choice
        print("\nChoose testing mode:")
        print("1. Full SDK pipeline (recommended)")
        print("2. Individual extractor")
        
        choice = input("Enter choice (1 or 2, default=1): ").strip() or "1"
        
        if choice == "1":
            test_full_pipeline(text)
        elif choice == "2":
            extractor_name = input("Enter extractor name (invoice/address/contact/product/order/log_event/calendar_event/payment/measurement/people): ").strip().lower()
            test_individual_extractor(extractor_name, text)
        else:
            print("❌ Invalid choice")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Test data normalization SDK extractors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --text "Invoice #123 from Acme Corp"
  %(prog)s --extractor invoice --text "Invoice #A-1027 total: $100"
  %(prog)s --examples
  %(prog)s --interactive
        """
    )
    
    parser.add_argument(
        "--text", "-t",
        help="Text to extract data from"
    )
    
    parser.add_argument(
        "--extractor", "-e",
        choices=['invoice', 'address', 'contact', 'product', 'order', 'log_event', 'calendar_event', 'payment', 'measurement', 'people'],
        help="Test specific extractor (default: full pipeline)"
    )
    
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Test with example data from data_examples.json"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive testing mode"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Print header
    print("🏗️  Data Normalization SDK - Extractor Testing CLI")
    print("=" * 60)
    
    # Handle different modes
    if args.examples:
        test_example_data()
    elif args.interactive:
        interactive_mode()
    elif args.text:
        if args.extractor:
            test_individual_extractor(args.extractor, args.text)
        else:
            test_full_pipeline(args.text)
    else:
        # No arguments provided, show help and start interactive mode
        parser.print_help()
        print("\n💡 Starting interactive mode...")
        interactive_mode()


if __name__ == "__main__":
    main()