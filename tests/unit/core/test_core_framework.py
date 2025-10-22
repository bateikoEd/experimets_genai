"""
Test the core framework functionality.
"""

import pytest
from src.data_normalization_sdk.core import (
    DataNormalizationSDK, EntityType, EntityResult, ProcessingMetadata,
    BaseExtractor, SDKConfig
)
from typing import Set, Tuple, Dict, Any


class TestExtractor(BaseExtractor):
    """Test extractor for testing purposes."""
    
    @property
    def supported_entity_types(self) -> Set[EntityType]:
        return {EntityType.INVOICE}
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        # Simple test extraction
        if "invoice" in text.lower():
            return {"test_field": "test_value"}, 0.9
        return {"test_field": "test_value"}, 0.3
    
    def get_name(self) -> str:
        return "test_extractor"


def test_sdk_initialization():
    """Test that SDK initializes correctly."""
    sdk = DataNormalizationSDK()
    assert sdk.config is not None
    assert isinstance(sdk.config, SDKConfig)


def test_sdk_with_custom_extractor():
    """Test that SDK can register and use custom extractors."""
    sdk = DataNormalizationSDK()
    
    # Register test extractor
    test_extractor = TestExtractor()
    sdk.register_extractor(test_extractor)
    
    # Verify it's registered
    extractors = sdk.extractors.get_extractors_for_entity_type(EntityType.INVOICE)
    assert len(extractors) >= 1
    assert any(e.get_name() == "test_extractor" for e in extractors)


def test_entity_type_enum():
    """Test that EntityType enum works correctly."""
    # Test all expected entity types exist
    expected_types = [
        "invoice", "address", "contact", "product", "order",
        "log_event", "event", "payment", "spec", "person"
    ]
    
    for type_name in expected_types:
        entity_type = EntityType(type_name)
        assert entity_type.value == type_name


def test_processing_metadata():
    """Test ProcessingMetadata validation."""
    # Valid metadata
    metadata = ProcessingMetadata(
        confidence=0.85,
        transformations=["extraction", "normalization"]
    )
    assert metadata.confidence == 0.85
    assert "extraction" in metadata.transformations
    
    # Invalid confidence should raise error
    with pytest.raises(ValueError):
        ProcessingMetadata(confidence=1.5, transformations=[])
    
    with pytest.raises(ValueError):
        ProcessingMetadata(confidence=-0.1, transformations=[])


if __name__ == "__main__":
    # Run basic tests
    test_sdk_initialization()
    test_sdk_with_custom_extractor()
    test_entity_type_enum()
    test_processing_metadata()
    print("All core framework tests passed!")