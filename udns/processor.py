"""
Main UDNS processor that orchestrates parsing, normalization, and cleaning.
"""

import re
from typing import Dict, Any, Optional, List, Type
from .core import EntityType, NormalizedEntity
from .parsers import (
    DomainParser, InvoiceParser, AddressParser, ContactParser, 
    ProductParser, PersonParser
)
from .validators import UDNSValidator
from .cleaners.pipeline import CleaningPipeline
from .cleaners.registry import CleaningPluginRegistry
from .cleaners.config import CleaningConfig


class UDNSProcessor:
    """Main processor for Universal Data Normalization Specification."""
    
    def __init__(self, enable_validation: bool = True, enable_cleaning: bool = True,
                 cleaning_config: Optional[CleaningConfig] = None):
        """
        Initialize the UDNS processor.
        
        Args:
            enable_validation: Whether to enable schema validation
            enable_cleaning: Whether to enable data cleaning
            cleaning_config: Optional cleaning configuration
        """
        self.enable_validation = enable_validation
        self.enable_cleaning = enable_cleaning
        self.validator = UDNSValidator() if enable_validation else None
        
        # Initialize cleaning components
        if enable_cleaning:
            self.cleaning_pipeline = CleaningPipeline(config=cleaning_config)
        
        # Register domain parsers
        self.parsers: Dict[EntityType, DomainParser] = {
            EntityType.INVOICE: InvoiceParser(),
            EntityType.ADDRESS: AddressParser(),
            EntityType.CONTACT: ContactParser(),
            EntityType.PRODUCT: ProductParser(),
            EntityType.PERSON: PersonParser(),
        }
        
        # Keywords for entity type detection
        self.entity_keywords = {
            EntityType.INVOICE: [
                'invoice', 'bill', 'receipt', 'vendor', 'total', 'vat', 'tax'
            ],
            EntityType.ADDRESS: [
                'bill to', 'ship to', 'address', 'street', 'city', 'postal', 'zip'
            ],
            EntityType.CONTACT: [
                'phone', 'email', 'contact', 'support', 'ext', 'extension'
            ],
            EntityType.PRODUCT: [
                'name', 'price', 'category', 'weight', 'product', 'item'
            ],
            EntityType.PERSON: [
                'prof.', 'dr.', 'mr.', 'mrs.', 'ms.', 'cto', 'ceo', 'manager'
            ],
            EntityType.ORDER: [
                'items', 'sku', 'quantity', 'ship by', 'order', 'lines'
            ],
            EntityType.LOG_EVENT: [
                'warn', 'error', 'info', 'debug', 'log', 'timestamp', 'utc'
            ],
            EntityType.EVENT: [
                'meeting', 'standup', 'event', 'calendar', 'timezone'
            ],
            EntityType.PAYMENT: [
                'paid', 'payment', 'card', 'cash', 'transaction', 'auth'
            ],
            EntityType.SPEC: [
                'spec', 'dimensions', 'weight', 'inches', 'cm', 'measurement'
            ]
        }
    
    
    def detect_entity_type(self, input_text: str) -> EntityType:
        """
        Detect the most likely entity type from input text.
        
        Args:
            input_text: Input text to analyze
            
        Returns:
            Detected EntityType
        """
        text_lower = input_text.lower()
        scores = {}
        
        for entity_type, keywords in self.entity_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            scores[entity_type] = score
        
        # Return entity type with highest score
        if scores:
            best_entity = max(scores, key=scores.get)
            if scores[best_entity] > 0:
                return best_entity
        
        # Default fallback based on patterns
        if re.search(r'invoice|bill|receipt', text_lower):
            return EntityType.INVOICE
        elif re.search(r'@|phone|\+\d', text_lower):
            return EntityType.CONTACT
        elif re.search(r'prof\.|dr\.|mr\.|mrs\.', text_lower):
            return EntityType.PERSON
        elif re.search(r'address|street|city', text_lower):
            return EntityType.ADDRESS
        elif re.search(r'price|€|£|\$', text_lower):
            return EntityType.PRODUCT
        
        # Default to contact if no clear indicators
        return EntityType.CONTACT
    
    def process(
        self, 
        input_text: str, 
        entity_type: Optional[EntityType] = None,
        enable_cleaning: Optional[bool] = None,
        cleaning_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NormalizedEntity:
        """
        Process input text and return normalized entity.
        
        Args:
            input_text: Text to process
            entity_type: Optional explicit entity type
            enable_cleaning: Override default cleaning setting
            cleaning_config: Configuration for cleaning pipeline
            **kwargs: Additional arguments passed to parser
            
        Returns:
            NormalizedEntity with processed data
            
        Raises:
            ValueError: If processing fails
            ValidationError: If validation is enabled and fails
        """
        if not input_text.strip():
            raise ValueError("Input text cannot be empty")
        
        # Determine cleaning setting
        use_cleaning = enable_cleaning if enable_cleaning is not None else self.enable_cleaning
        
        # Detect entity type if not provided
        if entity_type is None:
            entity_type = self.detect_entity_type(input_text)
        
        # Get appropriate parser
        parser = self.parsers.get(entity_type)
        if not parser:
            raise ValueError(f"No parser available for entity type: {entity_type}")
        
        # Parse the input
        try:
            entity = parser.parse(input_text, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to parse {entity_type.value}: {str(e)}")
        
        # Apply cleaning if enabled
        if use_cleaning and self.cleaning_pipeline:
            import time
            start_time = time.time()
            
            try:
                # Clean the entity attributes
                cleaned_attributes = self.cleaning_pipeline.process(
                    entity.attributes,
                    entity_type,
                    cleaning_config
                )
                
                # Update entity with cleaned attributes
                entity.attributes = cleaned_attributes.cleaned_data
                
                # Update cleaning metadata
                entity.metadata.cleaning_enabled = True
                entity.metadata.cleaning_pipeline_version = "1.0.0"
                entity.metadata.cleaning_duration_ms = (time.time() - start_time) * 1000
                
                # Add cleaning operations to metadata
                if cleaned_attributes.operations:
                    for op in cleaned_attributes.operations:
                        entity.metadata.add_cleaning_operation(op.description, op.success)
                
                # Set cleaning statistics
                if cleaned_attributes.stats:
                    entity.metadata.set_cleaning_stats(cleaned_attributes.stats.to_dict())
                
                # Update confidence if cleaning improved data quality
                if cleaned_attributes.stats.success_rate > 0:
                    entity.metadata.confidence = min(1.0, entity.metadata.confidence + 0.1)
                
            except Exception as e:
                # Log cleaning error but continue processing
                entity.metadata.add_cleaning_error(str(e))
                entity.metadata.transformations.append(f"cleaning_error: {str(e)}")
        
        # Validate if enabled
        if self.enable_validation and self.validator:
            entity_dict = entity.to_dict()
            validation_errors = self.validator.validate_entity(entity_dict)
            if validation_errors:
                raise ValueError(f"Validation failed: {'; '.join(validation_errors)}")
        
        return entity
    
    def process_batch(
        self, 
        inputs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple inputs in batch.
        
        Args:
            inputs: List of input dictionaries with keys:
                   - 'text': input text
                   - 'entity_type': optional entity type
                   - 'enable_cleaning': optional cleaning override
                   - 'cleaning_config': optional cleaning configuration
                   - 'id': optional identifier
        
        Returns:
            List of results with success/error information
        """
        results = []
        
        for i, input_data in enumerate(inputs):
            result = {
                'id': input_data.get('id', f'input_{i}'),
                'success': False,
                'entity': None,
                'error': None
            }
            
            try:
                text = input_data.get('text', '')
                entity_type_str = input_data.get('entity_type')
                entity_type = EntityType(entity_type_str) if entity_type_str else None
                enable_cleaning = input_data.get('enable_cleaning')
                cleaning_config = input_data.get('cleaning_config', {})
                
                entity = self.process(
                    text, 
                    entity_type, 
                    enable_cleaning=enable_cleaning,
                    cleaning_config=cleaning_config
                )
                result['success'] = True
                result['entity'] = entity.to_dict()
                
            except Exception as e:
                result['error'] = str(e)
            
            results.append(result)
        
        return results
    
    def get_supported_entity_types(self) -> List[str]:
        """Get list of supported entity types."""
        return [et.value for et in self.parsers.keys()]
    
    def add_parser(self, entity_type: EntityType, parser: DomainParser):
        """
        Add or replace a parser for an entity type.
        
        Args:
            entity_type: Entity type to register
            parser: Parser instance
        """
        self.parsers[entity_type] = parser
    
    def set_cleaning_config(self, config: CleaningConfig):
        """
        Set global cleaning configuration.
        
        Args:
            config: Cleaning configuration instance
        """
        if self.cleaning_pipeline:
            self.cleaning_pipeline.set_config(config)
    
    def load_cleaning_config(self, config_name: str):
        """
        Load a cleaning configuration by name.
        
        Args:
            config_name: Name of configuration to load
        """
        if self.cleaning_pipeline:
            self.cleaning_pipeline.load_config(config_name)
    
    def get_cleaning_stats(self) -> Dict[str, Any]:
        """
        Get cleaning statistics and metrics.
        
        Returns:
            Dictionary with cleaning statistics
        """
        if not self.cleaning_pipeline:
            return {}
        
        return self.cleaning_pipeline.get_stats()
    
    def get_cleaning_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current cleaning configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        if not self.cleaning_pipeline:
            return {}
        
        return self.cleaning_pipeline.get_config_summary()
    
    def update_cleaner_config(self, cleaner_name: str, **kwargs):
        """
        Update configuration for a specific cleaner.
        
        Args:
            cleaner_name: Name of the cleaner
            **kwargs: Configuration parameters to update
        """
        if self.cleaning_pipeline:
            self.cleaning_pipeline.update_cleaner_config(cleaner_name, **kwargs)
    
    def update_entity_config(self, entity_type: str, **kwargs):
        """
        Update configuration for a specific entity type.
        
        Args:
            entity_type: Entity type name
            **kwargs: Configuration parameters to update
        """
        if self.cleaning_pipeline:
            self.cleaning_pipeline.update_entity_config(entity_type, **kwargs)
    
    def set_confidence_threshold(self, threshold: float):
        """
        Set minimum confidence threshold for accepting results.
        
        Args:
            threshold: Confidence threshold (0.0 - 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        self.confidence_threshold = threshold