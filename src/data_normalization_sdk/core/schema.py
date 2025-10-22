"""
Schema definitions for the Data Normalization SDK.

This module defines the data structures and schemas used throughout
the SDK for consistent data representation and validation.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

# Re-export the core types from base for convenience
from .base import EntityType, EntityResult, ProcessingMetadata


@dataclass
class PersonName:
    """Structured representation of a person's name."""
    
    given_name: Optional[str] = None
    middle_name: Optional[str] = None
    family_name: Optional[str] = None
    full_name: Optional[str] = None
    ascii_full_name: Optional[str] = None
    honorific: Optional[str] = None


@dataclass
class Address:
    """Structured representation of a physical address."""
    
    street_address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country_name: Optional[str] = None
    country_code: Optional[str] = None
    person: Optional[PersonName] = None


@dataclass
class ContactInfo:
    """Structured representation of contact information."""
    
    phone_e164: Optional[str] = None
    phone_extension: Optional[str] = None
    email: Optional[str] = None
    country_code_inferred: Optional[str] = None


@dataclass
class Dimensions:
    """Structured representation of physical dimensions."""
    
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None


@dataclass
class OrderLineItem:
    """Structured representation of an order line item."""
    
    sku: Optional[str] = None
    name: Optional[str] = None
    variant: Optional[str] = None
    quantity: Optional[int] = None


# Schema validation templates for each entity type
ENTITY_SCHEMAS: Dict[EntityType, Dict[str, Any]] = {
    EntityType.INVOICE: {
        "required_fields": ["invoice_number", "total_amount"],
        "optional_fields": [
            "vendor_name", "invoice_date", "currency_code", "tax_rate_percent"
        ],
        "field_types": {
            "invoice_number": str,
            "vendor_name": str,
            "invoice_date": str,  # ISO 8601 string
            "total_amount": (int, float, Decimal),
            "currency_code": str,
            "tax_rate_percent": (int, float)
        }
    },
    
    EntityType.ADDRESS: {
        "required_fields": ["street_address"],
        "optional_fields": [
            "person", "district", "city", "region", "postal_code", 
            "country_name", "country_code"
        ],
        "field_types": {
            "person": (dict, PersonName),
            "street_address": str,
            "district": str,
            "city": str,
            "region": str,
            "postal_code": str,
            "country_name": str,
            "country_code": str
        }
    },
    
    EntityType.CONTACT: {
        "required_fields": [],  # At least one contact method required (validated separately)
        "optional_fields": [
            "phone_e164", "phone_extension", "email", "country_code_inferred"
        ],
        "field_types": {
            "phone_e164": str,
            "phone_extension": str,
            "email": str,
            "country_code_inferred": str
        }
    },
    
    EntityType.PRODUCT: {
        "required_fields": ["name"],
        "optional_fields": [
            "net_weight_kg", "price", "currency_code", "category_path"
        ],
        "field_types": {
            "name": str,
            "net_weight_kg": (int, float),
            "price": (int, float, Decimal),
            "currency_code": str,
            "category_path": list
        }
    },
    
    EntityType.ORDER: {
        "required_fields": ["lines"],
        "optional_fields": ["requested_ship_date"],
        "field_types": {
            "lines": list,
            "requested_ship_date": str  # ISO 8601 string
        }
    },
    
    EntityType.LOG_EVENT: {
        "required_fields": ["level", "timestamp"],
        "optional_fields": [
            "component", "user_id", "ip", "message"
        ],
        "field_types": {
            "level": str,
            "component": str,
            "timestamp": str,  # ISO 8601 string
            "user_id": str,
            "ip": str,
            "message": str
        }
    },
    
    EntityType.EVENT: {
        "required_fields": ["title", "start"],
        "optional_fields": [
            "end", "duration_minutes", "timezone"
        ],
        "field_types": {
            "title": str,
            "start": str,  # ISO 8601 string with timezone
            "end": str,    # ISO 8601 string with timezone
            "duration_minutes": (int, float),
            "timezone": str
        }
    },
    
    EntityType.PAYMENT: {
        "required_fields": ["amount", "currency_code"],
        "optional_fields": [
            "amount_in_minor_units", "method", "authorized_code", "paid_at"
        ],
        "field_types": {
            "amount": (int, float, Decimal),
            "currency_code": str,
            "amount_in_minor_units": int,
            "method": str,
            "authorized_code": str,
            "paid_at": str  # ISO 8601 string with timezone
        }
    },
    
    EntityType.SPEC: {
        "required_fields": [],  # At least one measurement required (validated separately)
        "optional_fields": [
            "dimensions_in", "dimensions_cm", "weight_lb", "weight_kg"
        ],
        "field_types": {
            "dimensions_in": (dict, Dimensions),
            "dimensions_cm": (dict, Dimensions),
            "weight_lb": (int, float),
            "weight_kg": (int, float)
        }
    },
    
    EntityType.PERSON: {
        "required_fields": ["full_name"],
        "optional_fields": [
            "honorific", "ascii_full_name", "role", "email", 
            "phone_e164", "country_code_inferred"
        ],
        "field_types": {
            "honorific": str,
            "full_name": str,
            "ascii_full_name": str,
            "role": str,
            "email": str,
            "phone_e164": str,
            "country_code_inferred": str
        }
    }
}


def validate_entity_schema(entity_result: EntityResult) -> List[str]:
    """Validate an entity result against its schema definition.
    
    Args:
        entity_result: The entity result to validate.
        
    Returns:
        List of validation error messages. Empty list if valid.
    """
    errors: List[str] = []
    entity_type = entity_result.entity_type
    attributes = entity_result.attributes
    
    if entity_type not in ENTITY_SCHEMAS:
        errors.append(f"Unknown entity type: {entity_type}")
        return errors
    
    schema = ENTITY_SCHEMAS[entity_type]
    
    # Check required fields
    for field in schema.get("required_fields", []):
        if field not in attributes or attributes[field] is None:
            errors.append(f"Required field '{field}' is missing or None")
    
    # Check field types
    field_types = schema.get("field_types", {})
    for field, value in attributes.items():
        if field in field_types and value is not None:
            expected_types = field_types[field]
            if not isinstance(expected_types, tuple):
                expected_types = (expected_types,)
            
            if not isinstance(value, expected_types):
                expected_names = [t.__name__ for t in expected_types]
                errors.append(
                    f"Field '{field}' has invalid type. "
                    f"Expected {expected_names}, got {type(value).__name__}"
                )
    
    # Entity-specific validation
    if entity_type == EntityType.CONTACT:
        # At least one contact method required
        contact_fields = ["phone_e164", "email"]
        if not any(attributes.get(field) for field in contact_fields):
            errors.append("At least one contact method (phone_e164 or email) is required")
    
    elif entity_type == EntityType.SPEC:
        # At least one measurement required
        measurement_fields = ["dimensions_in", "dimensions_cm", "weight_lb", "weight_kg"]
        if not any(attributes.get(field) for field in measurement_fields):
            errors.append("At least one measurement field is required")
    
    return errors


def create_entity_result(
    entity_type: EntityType,
    attributes: Dict[str, Any],
    confidence: float,
    transformations: List[str],
    **metadata_kwargs: Any
) -> EntityResult:
    """Create a properly structured EntityResult.
    
    Args:
        entity_type: The type of entity.
        attributes: Dictionary of entity attributes.
        confidence: Confidence score (0.0 to 1.0).
        transformations: List of transformations applied.
        **metadata_kwargs: Additional metadata fields.
        
    Returns:
        Properly structured EntityResult.
    """
    metadata = ProcessingMetadata(
        confidence=confidence,
        transformations=transformations,
        **metadata_kwargs
    )
    
    return EntityResult(
        entity_type=entity_type,
        attributes=attributes,
        metadata=metadata
    )