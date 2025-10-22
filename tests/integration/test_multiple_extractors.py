#!/usr/bin/env python3
"""Test multiple extractors with real data examples."""

import json
from pathlib import Path
from data_normalization_sdk.core.sdk import DataNormalizationSDK


def test_multiple_extractors():
    """Test address, contact, product, and order extractors."""
    # Load data examples
    data_file = Path(__file__).parent.parent.parent / "data" / "data_examples.json"
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Initialize SDK
    sdk = DataNormalizationSDK()
    
    # Test examples by domain
    test_cases = [
        ("addresses", "EX02"),
        ("contacts", "EX03"), 
        ("products", "EX04"),
        ("orders", "EX05")
    ]
    
    print("Testing multiple extractors...")
    
    for domain, example_id in test_cases:
        # Find the example
        example = next((ex for ex in data['examples'] if ex['id'] == example_id), None)
        if not example:
            print(f"Example {example_id} not found!")
            continue
            
        print(f"\n--- Testing {domain} ({example_id}) ---")
        print(f"Input: {example['input_text']}")
        
        # Process with SDK
        result = sdk.process(example['input_text'])
        
        if result:
            print(f"Result entity type: {result.entity_type}")
            print(f"Result confidence: {result.metadata.confidence:.3f}")
            print(f"Result attributes: {result.attributes}")
            print(f"Transformations: {result.metadata.transformations}")
        else:
            print("No result returned")
    
    print(f"\nMultiple extractors test completed!")


if __name__ == "__main__":
    test_multiple_extractors()