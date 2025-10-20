"""
Core data structures for UDNS implementation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class EntityType(Enum):
    """Enumeration of supported entity types in UDNS."""
    INVOICE = "invoice"
    ADDRESS = "address"
    CONTACT = "contact"
    PRODUCT = "product"
    ORDER = "order"
    LOG_EVENT = "log_event"
    EVENT = "event"
    PAYMENT = "payment"
    SPEC = "spec"
    PERSON = "person"


@dataclass
class Metadata:
    """Metadata container for UDNS normalized entities."""
    confidence: float
    parser_version: Optional[str] = None
    source: Optional[str] = None
    locale_hint: Optional[str] = None
    locale_detected: Optional[str] = None
    transformations: Optional[List[str]] = field(default_factory=list)
    standard: Optional[str] = None
    normalization_ruleset: Optional[str] = None
    schema: Optional[str] = None
    timezone_source: Optional[str] = None
    heuristics: Optional[List[str]] = field(default_factory=list)
    conversions: Optional[Dict[str, float]] = field(default_factory=dict)
    precision: Optional[int] = None
    
    def __post_init__(self):
        """Validate confidence score."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class NormalizedEntity:
    """Main container for normalized data following UDNS specification."""
    entity_type: EntityType
    attributes: Dict[str, Any]
    metadata: Metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "entity_type": self.entity_type.value,
            "attributes": self.attributes,
            "metadata": {
                k: v for k, v in self.metadata.__dict__.items() 
                if v is not None
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NormalizedEntity':
        """Create instance from dictionary."""
        entity_type = EntityType(data["entity_type"])
        attributes = data["attributes"]
        metadata_dict = data["metadata"]
        
        metadata = Metadata(
            confidence=metadata_dict["confidence"],
            **{k: v for k, v in metadata_dict.items() if k != "confidence"}
        )
        
        return cls(
            entity_type=entity_type,
            attributes=attributes,
            metadata=metadata
        )


# Domain-specific attribute dataclasses
@dataclass
class PersonName:
    """Structured person name."""
    given_name: str
    family_name: str
    middle_name: Optional[str] = None
    honorific: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get full name string."""
        parts = [self.honorific, self.given_name, self.middle_name, self.family_name]
        return " ".join(filter(None, parts))


@dataclass
class OrderLine:
    """Order line item."""
    sku: str
    name: str
    quantity: int
    variant: Optional[str] = None


@dataclass
class Dimensions:
    """Physical dimensions."""
    length: float
    width: float
    height: float
    unit: str = "cm"