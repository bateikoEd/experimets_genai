"""
Universal Data Normalization Specification (UDNS) v1.0
Implementation of the OpenSpec proposal for standardized data normalization.
"""

from .core import NormalizedEntity, EntityType, Metadata
from .processor import UDNSProcessor
from .validators import UDNSValidator
from .normalizers import DataNormalizer

__version__ = "1.0.0"
__author__ = "Eduard Bateiko"

__all__ = [
    "NormalizedEntity",
    "EntityType", 
    "Metadata",
    "UDNSProcessor",
    "UDNSValidator",
    "DataNormalizer"
]