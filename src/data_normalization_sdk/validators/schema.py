"""
Schema validator for entity validation.

This module implements validation of entity results against their schemas.
"""

from typing import Any, Dict, List, Set, Tuple

from ..core.base import BaseValidator, EntityType, EntityResult
from ..core.schema import validate_entity_schema


class SchemaValidator(BaseValidator):
    """Validator that checks entity results against their schemas."""
    
    @property
    def supported_entity_types(self) -> Set[EntityType]:
        # This validator works with all entity types
        return set(EntityType)
    
    def validate(self, entity_result: EntityResult) -> Tuple[bool, List[str], float]:
        """Validate entity result against schema.
        
        Args:
            entity_result: Complete entity result to validate.
            
        Returns:
            Tuple of (is_valid, validation_errors, confidence)
        """
        # Use the built-in schema validation
        validation_errors = validate_entity_schema(entity_result)
        
        is_valid = len(validation_errors) == 0
        
        # Calculate confidence based on validation success
        if is_valid:
            confidence = 1.0
        else:
            # Reduce confidence based on number of errors
            confidence = max(0.1, 1.0 - (len(validation_errors) * 0.2))
        
        return is_valid, validation_errors, confidence
    
    def get_name(self) -> str:
        return "schema_validator"