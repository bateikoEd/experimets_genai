"""
Date normalization functionality.

This module implements ISO 8601 date normalization for extracted date fields.
"""

import re
from typing import Any, Dict, Set, Tuple
from datetime import datetime
from dateutil import parser as date_parser

from ..core.base import BaseNormalizer, EntityType, ProcessingMetadata


class DateNormalizer(BaseNormalizer):
    """Normalizer for date fields to ISO 8601 format."""
    
    def __init__(self, config: Dict[str, Any] = None) -> None:
        super().__init__(config)
        
        # Date format preferences
        self._date_preference = self.config.get('ambiguous_date_preference', 'dmy')  # day-month-year
    
    @property
    def supported_entity_types(self) -> Set[EntityType]:
        # This normalizer works with all entity types that have date fields
        return {
            EntityType.INVOICE, EntityType.ORDER, EntityType.LOG_EVENT, 
            EntityType.EVENT, EntityType.PAYMENT
        }
    
    def normalize(self, extracted_data: Dict[str, Any], entity_type: EntityType) -> Tuple[Dict[str, Any], ProcessingMetadata]:
        """Normalize date fields in extracted data.
        
        Args:
            extracted_data: Raw extracted data.
            entity_type: The entity type being normalized.
            
        Returns:
            Tuple of (normalized_data, metadata)
        """
        normalized_data = extracted_data.copy()
        transformations = []
        confidence = 1.0
        
        # Define date fields per entity type
        date_fields = self._get_date_fields_for_entity_type(entity_type)
        
        for field_name in date_fields:
            if field_name in extracted_data and extracted_data[field_name]:
                raw_date = extracted_data[field_name]
                
                try:
                    # Parse the date string
                    if isinstance(raw_date, str):
                        # Handle ambiguous date formats based on preference
                        if self._date_preference == 'dmy':
                            # Day-month-year preference (European style)
                            parsed_date = date_parser.parse(raw_date, dayfirst=True)
                        else:
                            # Month-day-year preference (US style)  
                            parsed_date = date_parser.parse(raw_date, dayfirst=False)
                        
                        # Convert to ISO 8601 format
                        iso_date = parsed_date.strftime('%Y-%m-%d')
                        normalized_data[field_name] = iso_date
                        transformations.append(f"normalized_{field_name}_to_iso8601")
                        
                except (ValueError, TypeError) as e:
                    # Could not parse date, leave original and reduce confidence
                    confidence *= 0.7
                    transformations.append(f"failed_to_normalize_{field_name}")
        
        metadata = ProcessingMetadata(
            confidence=confidence,
            transformations=transformations,
            standard="ISO_8601"
        )
        
        return normalized_data, metadata
    
    def _get_date_fields_for_entity_type(self, entity_type: EntityType) -> Set[str]:
        """Get the date field names for a specific entity type."""
        field_mapping = {
            EntityType.INVOICE: {'invoice_date'},
            EntityType.ORDER: {'requested_ship_date'},
            EntityType.LOG_EVENT: {'timestamp'},
            EntityType.EVENT: {'start', 'end'},
            EntityType.PAYMENT: {'paid_at'}
        }
        
        return field_mapping.get(entity_type, set())
    
    def get_name(self) -> str:
        return "date_normalizer"