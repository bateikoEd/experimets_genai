"""
Test the complete SDK pipeline with invoice data.
"""

import json
from pathlib import Path
from data_normalization_sdk import DataNormalizationSDK, EntityType


def test_invoice_processing():
    """Test processing of invoice data from data_examples.json."""
    
    # Load the test data
    data_file = Path(__file__).parent.parent.parent / "data" / "data_examples.json"
    
    with open(data_file, 'r') as f:
        test_data = json.load(f)
    
    # Find the invoice example
    invoice_example = None
    for example in test_data["examples"]:
        if example["domain"] == "invoices":
            invoice_example = example
            break
    
    assert invoice_example is not None, "Invoice example not found in test data"
    
    # Initialize SDK
    sdk = DataNormalizationSDK()
    
    # Process the invoice text
    input_text = invoice_example["input_text"]
    print(f"Processing: {input_text}")
    
    result = sdk.process(input_text)
    
    print(f"Result entity type: {result.entity_type}")
    print(f"Result confidence: {result.metadata.confidence}")
    print(f"Result attributes: {result.attributes}")
    print(f"Transformations: {result.metadata.transformations}")
    
    # Verify basic expectations
    assert result.entity_type == EntityType.INVOICE
    assert result.metadata.confidence > 0.0
    assert "invoice_number" in result.attributes
    
    print("Invoice processing test passed!")
    return result


if __name__ == "__main__":
    test_invoice_processing()