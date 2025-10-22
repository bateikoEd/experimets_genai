"""
Data Normalization SDK

A Python SDK for extracting and normalizing unstructured text data 
into standardized, structured formats with international standards compliance.

This package provides:
- Unified API for processing multiple entity types
- Standards-compliant normalization (ISO 8601, ISO 4217, E.164)
- Confidence scoring and metadata tracking
- Pluggable architecture for custom extractors and normalizers
"""

from .core.sdk import DataNormalizationSDK
from .core.base import BaseExtractor, BaseNormalizer, BaseValidator
from .core.schema import EntityResult, EntityType, ProcessingMetadata
from .core.config import SDKConfig

__version__ = "0.1.0"
__author__ = "Eduard Bateiko"
__email__ = "eduard.bateiko@example.com"

__all__ = [
    # Main SDK interface
    "DataNormalizationSDK",
    
    # Base classes for extensions
    "BaseExtractor",
    "BaseNormalizer", 
    "BaseValidator",
    
    # Core data structures
    "EntityResult",
    "EntityType",
    "ProcessingMetadata",
    
    # Configuration
    "SDKConfig",
    
    # Package metadata
    "__version__",
    "__author__",
    "__email__",
]