"""
Dictionary cleaning utilities for UDNS data cleaning.
"""

from typing import Any, List, Dict, Set, Optional
from .base import BaseCleaner, CleaningContext, CleanResult, CleaningOperation, CleaningOperationType
from .text import TextCleaner


class DictionaryTextCleaner(BaseCleaner):
    """Cleaner that applies text cleaning to dictionary fields."""
    
    def __init__(self, target_fields: Optional[List[str]] = None,
                 text_cleaner_config: Optional[Dict] = None):
        super().__init__("dictionary_text_cleaner", "1.0.0")
        self.target_fields = target_fields or ['text', 'name', 'description', 'title', 'label']
        self.text_cleaner_config = text_cleaner_config or {}
        self.text_cleaner = TextCleaner(**self.text_cleaner_config)
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean text fields in a dictionary."""
        if not isinstance(data, dict):
            return CleanResult(data, [])
        
        original_data = data.copy()
        operations = []
        
        try:
            cleaned_data = {}
            
            # Handle empty dictionary - return success
            if not data:
                return CleanResult(cleaned_data, operations, context)
            
            for field, value in data.items():
                # Apply text cleaning to target fields
                if field in self.target_fields and isinstance(value, str):
                    # Create child context for this field
                    field_context = context.create_child_context()
                    field_context.field = field
                    
                    # Clean the text
                    text_result = self.text_cleaner.clean(value, field_context)
                    
                    cleaned_data[field] = text_result.cleaned_data
                    operations.extend(text_result.operations)
                    
                    # Update context with field stats
                    if field_context.stats:
                        context.stats.merge(field_context.stats)
                else:
                    # Keep non-target fields and non-string values as-is
                    cleaned_data[field] = value
            
            return CleanResult(cleaned_data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="dictionary",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Dictionary text cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.target_fields is not None:
            if not isinstance(self.target_fields, list):
                errors.append("target_fields must be a list")
            else:
                for field in self.target_fields:
                    if not isinstance(field, str):
                        errors.append(f"target_fields contains non-string field: {field}")
        
        # Validate text cleaner config
        text_errors = self.text_cleaner.validate_config()
        errors.extend(f"text_cleaner.{error}" for error in text_errors)
        
        return errors


class FieldSpecificCleaner(BaseCleaner):
    """Cleaner that applies different cleaners to different fields."""
    
    def __init__(self, field_configs: Dict[str, Dict]):
        """
        Initialize field-specific cleaner.
        
        Args:
            field_configs: Dictionary mapping field names to cleaner configurations
                          Format: {field_name: {'cleaner_type': 'text', 'config': {...}}}
        """
        super().__init__("field_specific_cleaner", "1.0.0")
        self.field_configs = field_configs
        self.field_cleaners = {}
        
        # Initialize cleaners for each field
        for field, config in field_configs.items():
            cleaner_type = config.get('cleaner_type', 'text')
            cleaner_config = config.get('config', {})
            
            if cleaner_type == 'text':
                self.field_cleaners[field] = TextCleaner(**cleaner_config)
            else:
                # TODO: Add support for other cleaner types
                raise ValueError(f"Unsupported cleaner type: {cleaner_type}")
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean specific fields in a dictionary."""
        if not isinstance(data, dict):
            return CleanResult(data, [])
        
        original_data = data.copy()
        operations = []
        
        try:
            cleaned_data = {}
            
            for field, value in data.items():
                # Apply field-specific cleaning if configured
                if field in self.field_cleaners and isinstance(value, str):
                    # Create child context for this field
                    field_context = context.create_child_context()
                    field_context.field = field
                    
                    # Clean the field
                    cleaner = self.field_cleaners[field]
                    field_result = cleaner.clean(value, field_context)
                    
                    cleaned_data[field] = field_result.cleaned_data
                    operations.extend(field_result.operations)
                    
                    # Update context with field stats
                    if field_context.stats:
                        context.stats.merge(field_context.stats)
                else:
                    # Keep non-configured fields and non-string values as-is
                    cleaned_data[field] = value
            
            return CleanResult(cleaned_data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="field_specific",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Field-specific cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        
        for field, config in self.field_configs.items():
            if not isinstance(config, dict):
                errors.append(f"Field '{field}' config must be a dictionary")
                continue
            
            cleaner_type = config.get('cleaner_type')
            if cleaner_type not in ['text']:
                errors.append(f"Field '{field}' has unsupported cleaner_type: {cleaner_type}")
            
            cleaner_config = config.get('config', {})
            if cleaner_type == 'text':
                if field not in self.field_cleaners:
                    errors.append(f"Field '{field}' text cleaner not initialized")
                else:
                    text_errors = self.field_cleaners[field].validate_config()
                    errors.extend(f"Field '{field}.{error}" for error in text_errors)
        
        return errors