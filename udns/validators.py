"""
JSON Schema validators for UDNS entity types.
"""

import json
from typing import Dict, Any, List
from jsonschema import validate, ValidationError
from .core import EntityType


class UDNSValidator:
    """Validator for UDNS normalized entities."""
    
    def __init__(self):
        """Initialize validator with schemas."""
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[EntityType, Dict[str, Any]]:
        """Load JSON schemas for each entity type."""
        schemas = {}
        
        # Base schema structure
        base_schema = {
            "type": "object",
            "required": ["entity_type", "attributes", "metadata"],
            "properties": {
                "entity_type": {"type": "string"},
                "metadata": {
                    "type": "object",
                    "required": ["confidence"],
                    "properties": {
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0
                        },
                        "parser_version": {"type": "string"},
                        "source": {"type": "string"},
                        "locale_hint": {"type": "string"},
                        "locale_detected": {"type": "string"},
                        "transformations": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "standard": {"type": "string"},
                        "normalization_ruleset": {"type": "string"},
                        "schema": {"type": "string"}
                    },
                    "additionalProperties": True
                }
            },
            "additionalProperties": False
        }
        
        # Invoice schema
        schemas[EntityType.INVOICE] = {
            **base_schema,
            "properties": {
                **base_schema["properties"],
                "entity_type": {"const": "invoice"},
                "attributes": {
                    "type": "object",
                    "required": ["invoice_number", "vendor_name", "invoice_date", "total_amount", "currency_code"],
                    "properties": {
                        "invoice_number": {"type": "string"},
                        "vendor_name": {"type": "string"},
                        "invoice_date": {
                            "type": "string",
                            "pattern": r"^\d{4}-\d{2}-\d{2}$"
                        },
                        "total_amount": {"type": "number"},
                        "currency_code": {
                            "type": "string",
                            "pattern": r"^[A-Z]{3}$"
                        },
                        "tax_rate_percent": {"type": "number"}
                    },
                    "additionalProperties": False
                }
            }
        }
        
        # Address schema
        schemas[EntityType.ADDRESS] = {
            **base_schema,
            "properties": {
                **base_schema["properties"],
                "entity_type": {"const": "address"},
                "attributes": {
                    "type": "object",
                    "required": ["street_address", "city", "country_name", "country_code"],
                    "properties": {
                        "person": {
                            "type": "object",
                            "required": ["given_name", "family_name"],
                            "properties": {
                                "given_name": {"type": "string"},
                                "middle_name": {"type": ["string", "null"]},
                                "family_name": {"type": "string"}
                            }
                        },
                        "street_address": {"type": "string"},
                        "district": {"type": ["string", "null"]},
                        "city": {"type": "string"},
                        "postal_code": {"type": "string"},
                        "region": {"type": ["string", "null"]},
                        "country_name": {"type": "string"},
                        "country_code": {
                            "type": "string",
                            "pattern": r"^[A-Z]{3}$"
                        }
                    },
                    "additionalProperties": False
                }
            }
        }
        
        # Contact schema
        schemas[EntityType.CONTACT] = {
            **base_schema,
            "properties": {
                **base_schema["properties"],
                "entity_type": {"const": "contact"},
                "attributes": {
                    "type": "object",
                    "properties": {
                        "phone_e164": {
                            "type": "string",
                            "pattern": r"^\+\d{1,15}$"
                        },
                        "phone_extension": {"type": "string"},
                        "email": {
                            "type": "string",
                            "format": "email"
                        },
                        "country_code_inferred": {
                            "type": "string",
                            "pattern": r"^[A-Z]{3}$"
                        }
                    },
                    "additionalProperties": False
                }
            }
        }
        
        # Product schema
        schemas[EntityType.PRODUCT] = {
            **base_schema,
            "properties": {
                **base_schema["properties"],
                "entity_type": {"const": "product"},
                "attributes": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "net_weight_kg": {"type": "number"},
                        "price": {"type": "number"},
                        "currency_code": {
                            "type": "string",
                            "pattern": r"^[A-Z]{3}$"
                        },
                        "category_path": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "additionalProperties": False
                }
            }
        }
        
        # Order schema
        schemas[EntityType.ORDER] = {
            **base_schema,
            "properties": {
                **base_schema["properties"],
                "entity_type": {"const": "order"},
                "attributes": {
                    "type": "object",
                    "required": ["lines"],
                    "properties": {
                        "lines": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["sku", "name", "quantity"],
                                "properties": {
                                    "sku": {"type": "string"},
                                    "name": {"type": "string"},
                                    "variant": {"type": "string"},
                                    "quantity": {"type": "integer", "minimum": 1}
                                }
                            }
                        },
                        "requested_ship_date": {
                            "type": "string",
                            "pattern": r"^\d{4}-\d{2}-\d{2}$"
                        }
                    },
                    "additionalProperties": False
                }
            }
        }
        
        # Person schema
        schemas[EntityType.PERSON] = {
            **base_schema,
            "properties": {
                **base_schema["properties"],
                "entity_type": {"const": "person"},
                "attributes": {
                    "type": "object",
                    "required": ["full_name"],
                    "properties": {
                        "honorific": {"type": "string"},
                        "full_name": {"type": "string"},
                        "ascii_full_name": {"type": "string"},
                        "role": {"type": "string"},
                        "email": {
                            "type": "string",
                            "format": "email"
                        },
                        "phone_e164": {
                            "type": "string",
                            "pattern": r"^\+\d{1,15}$"
                        },
                        "country_code_inferred": {
                            "type": "string",
                            "pattern": r"^[A-Z]{3}$"
                        }
                    },
                    "additionalProperties": False
                }
            }
        }
        
        return schemas
    
    def validate_entity(self, entity_data: Dict[str, Any]) -> List[str]:
        """
        Validate a normalized entity against its schema.
        
        Args:
            entity_data: Entity data dictionary
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            entity_type_str = entity_data.get("entity_type")
            if not entity_type_str:
                return ["Missing entity_type field"]
            
            try:
                entity_type = EntityType(entity_type_str)
            except ValueError:
                return [f"Unknown entity_type: {entity_type_str}"]
            
            if entity_type not in self.schemas:
                return [f"No schema defined for entity_type: {entity_type_str}"]
            
            schema = self.schemas[entity_type]
            validate(instance=entity_data, schema=schema)
            
        except ValidationError as e:
            errors.append(f"Validation error: {e.message}")
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
        
        return errors
    
    def is_valid(self, entity_data: Dict[str, Any]) -> bool:
        """
        Check if entity data is valid.
        
        Args:
            entity_data: Entity data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        return len(self.validate_entity(entity_data)) == 0