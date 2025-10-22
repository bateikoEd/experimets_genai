"""
Base classes and interfaces for the UDNS cleaning system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from enum import Enum

from ..core import EntityType


class CleaningOperationType(Enum):
    """Types of cleaning operations."""
    NORMALIZE = "normalize"
    STANDARDIZE = "standardize"
    VALIDATE = "validate"
    ENHANCE = "enhance"
    TRANSFORM = "transform"
    REMOVE = "remove"
    REPLACE = "replace"


@dataclass
class CleaningOperation:
    """Represents a single cleaning operation."""
    field: str
    operation_type: CleaningOperationType
    description: Optional[str] = None
    before_value: Optional[Any] = None
    after_value: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "field": self.field,
            "operation_type": self.operation_type.value,
            "description": self.description,
            "before_value": str(self.before_value) if self.before_value is not None else None,
            "after_value": str(self.after_value) if self.after_value is not None else None,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class CleaningStats:
    """Statistics for cleaning operations."""
    operations_count: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    processing_time_ms: float = 0.0
    fields_processed: List[str] = field(default_factory=list)
    operations: List[CleaningOperation] = field(default_factory=list)
    
    def add_operation(self, operation: CleaningOperation):
        """Add an operation to the statistics."""
        self.operations_count += 1
        self.operations.append(operation)
        
        if operation.success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1
        
        if operation.field not in self.fields_processed:
            self.fields_processed.append(operation.field)
    
    def merge(self, other: 'CleaningStats'):
        """Merge another CleaningStats into this one."""
        self.operations_count += other.operations_count
        self.successful_operations += other.successful_operations
        self.failed_operations += other.failed_operations
        self.processing_time_ms += other.processing_time_ms
        
        # Add unique fields
        for field in other.fields_processed:
            if field not in self.fields_processed:
                self.fields_processed.append(field)
        
        # Add all operations
        self.operations.extend(other.operations)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.operations_count == 0:
            return 0.0
        return self.successful_operations / self.operations_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "operations_count": self.operations_count,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "processing_time_ms": self.processing_time_ms,
            "success_rate": self.success_rate,
            "fields_processed": self.fields_processed,
            "operations": [op.to_dict() for op in self.operations]
        }
    
    def __getitem__(self, key: str) -> Any:
        """Make CleaningStats subscriptable for backward compatibility."""
        stats_dict = self.to_dict()
        if key == 'total_operations':
            return stats_dict['operations_count']
        elif key == 'success_rate':
            return stats_dict['success_rate']
        elif key == 'processing_time_ms':
            return stats_dict['processing_time_ms']
        else:
            return stats_dict[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in stats."""
        stats_dict = self.to_dict()
        if key == 'total_operations':
            return 'operations_count' in stats_dict
        elif key == 'success_rate':
            return 'success_rate' in stats_dict
        elif key == 'processing_time_ms':
            return 'processing_time_ms' in stats_dict
        else:
            return key in stats_dict


@dataclass
class CleaningContext:
    """Context information passed to cleaners during processing."""
    
    def __init__(self, entity_type: Optional[EntityType] = None, metadata: Optional[Dict[str, Any]] = None, field: Optional[str] = None):
        self.entity_type = entity_type
        self.metadata = metadata or {}
        self.config = {}
        self.stats = CleaningStats()
        self.input_data: Any = None
        self.output_data: Any = None
        self.parent_context: Optional['CleaningContext'] = None
        self.depth: int = 0
        self.field = field
    
    def set_input_data(self, data: Any):
        """Set the input data for this context."""
        self.input_data = data
    
    def set_output_data(self, data: Any):
        """Set the output data for this context."""
        self.output_data = data
    
    def create_child_context(self) -> 'CleaningContext':
        """Create a child context for nested cleaning operations."""
        child = CleaningContext(self.entity_type, self.metadata)
        child.config = self.config.copy()
        child.parent_context = self
        child.depth = self.depth + 1
        return child
    
    def add_operation(self, operation: CleaningOperation):
        """Add a cleaning operation to the context."""
        self.stats.add_operation(operation)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "entity_type": self.entity_type.value if self.entity_type else None,
            "metadata": self.metadata,
            "config": self.config,
            "stats": self.stats.to_dict(),
            "depth": self.depth,
            "input_data_preview": str(self.input_data)[:100] if self.input_data else None,
            "output_data_preview": str(self.output_data)[:100] if self.output_data else None
        }


@dataclass
class CleanResult:
    """Result of a cleaning operation."""
    
    def __init__(self, cleaned_data: Any, operations: List[CleaningOperation] = None, 
                 context: Optional[CleaningContext] = None):
        self.cleaned_data = cleaned_data
        self.operations = operations or []
        self.context = context or CleaningContext()
        
        # Set the cleaned data in the context
        self.context.set_output_data(cleaned_data)
        
        # Add all operations to context stats
        for operation in self.operations:
            self.context.add_operation(operation)
    
    @property
    def stats(self) -> CleaningStats:
        """Get cleaning statistics."""
        return self.context.stats
    
    @property
    def success(self) -> bool:
        """Check if cleaning was successful."""
        # If no operations, consider it successful (no changes needed)
        if len(self.operations) == 0:
            return True
        # Otherwise, check success rate
        return self.stats.success_rate > 0.5  # More than half successful
    
    def add_operation(self, operation: CleaningOperation):
        """Add an operation to the result."""
        self.operations.append(operation)
        self.context.add_operation(operation)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "cleaned_data": self.cleaned_data,
            "operations": [op.to_dict() for op in self.operations],
            "stats": self.stats.to_dict(),
            "context": self.context.to_dict(),
            "success": self.success
        }


class BaseCleaner(ABC):
    """Abstract base class for all data cleaners."""
    
    def __init__(self, name: Optional[str] = None, version: str = "1.0.0"):
        self._name = name or self.__class__.__name__
        self._version = version
        self._enabled = True
        self._config = {}
    
    @abstractmethod
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """
        Clean the input data and return result.
        
        Args:
            data: Input data to clean
            context: Cleaning context with metadata and configuration
            
        Returns:
            CleanResult containing cleaned data and operation details
        """
        pass
    
    @property
    def name(self) -> str:
        """Unique name for this cleaner."""
        return self._name
    
    @property
    def version(self) -> str:
        """Version of the cleaner implementation."""
        return self._version
    
    @property
    def enabled(self) -> bool:
        """Whether this cleaner is enabled."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        """Set whether this cleaner is enabled."""
        self._enabled = value
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get cleaner configuration."""
        return self._config.copy()
    
    @config.setter
    def config(self, value: Dict[str, Any]):
        """Set cleaner configuration."""
        self._config = value or {}
    
    def configure(self, **kwargs):
        """Configure the cleaner with parameters."""
        self._config.update(kwargs)
    
    def can_handle(self, data: Any, context: CleaningContext) -> bool:
        """
        Check if this cleaner can handle the given data.
        
        Args:
            data: Input data to check
            context: Cleaning context
            
        Returns:
            True if this cleaner can handle the data, False otherwise
        """
        return True  # Default implementation handles all data
    
    def validate_config(self) -> List[str]:
        """
        Validate the cleaner configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        return []  # Default implementation has no configuration requirements
    
    def pre_clean(self, data: Any, context: CleaningContext) -> Any:
        """
        Pre-processing hook before cleaning.
        
        Args:
            data: Input data
            context: Cleaning context
            
        Returns:
            Data to be passed to the main clean method
        """
        return data
    
    def post_clean(self, data: Any, context: CleaningContext) -> Any:
        """
        Post-processing hook after cleaning.
        
        Args:
            data: Cleaned data
            context: Cleaning context
            
        Returns:
            Final cleaned data
        """
        return data
    
    def __call__(self, data: Any, context: Optional[CleaningContext] = None) -> CleanResult:
        """
        Make the cleaner callable.
        
        Args:
            data: Input data to clean
            context: Optional cleaning context
            
        Returns:
            CleanResult
        """
        if context is None:
            context = CleaningContext()
        
        # Validate configuration
        errors = self.validate_config()
        if errors:
            # Create a failed result with configuration errors
            operations = [
                CleaningOperation(
                    field="config",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Configuration validation failed: {', '.join(errors)}",
                    success=False,
                    error_message=", ".join(errors)
                )
            ]
            return CleanResult(data, operations, context)
        
        # Check if cleaner is enabled
        if not self.enabled:
            operations = [
                CleaningOperation(
                    field="general",
                    operation_type=CleaningOperationType.VALIDATE,
                    description="Cleaner is disabled",
                    success=False,
                    error_message="Cleaner is disabled"
                )
            ]
            return CleanResult(data, operations, context)
        
        # Check if cleaner can handle the data
        if not self.can_handle(data, context):
            operations = [
                CleaningOperation(
                    field="general",
                    operation_type=CleaningOperationType.VALIDATE,
                    description="Cleaner cannot handle this data type",
                    success=False,
                    error_message="Data type not supported"
                )
            ]
            return CleanResult(data, operations, context)
        
        # Apply pre-processing
        try:
            processed_data = self.pre_clean(data, context)
        except Exception as e:
            operations = [
                CleaningOperation(
                    field="general",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Pre-processing failed: {str(e)}",
                    success=False,
                    error_message=str(e)
                )
            ]
            return CleanResult(data, operations, context)
        
        # Set input data in context
        context.set_input_data(processed_data)
        
        # Perform main cleaning
        try:
            result = self.clean(processed_data, context)
        except Exception as e:
            operations = [
                CleaningOperation(
                    field="general",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Cleaning failed: {str(e)}",
                    success=False,
                    error_message=str(e)
                )
            ]
            return CleanResult(data, operations, context)
        
        # Apply post-processing
        try:
            final_data = self.post_clean(result.cleaned_data, context)
            result.cleaned_data = final_data
        except Exception as e:
            operations = [
                CleaningOperation(
                    field="general",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Post-processing failed: {str(e)}",
                    success=False,
                    error_message=str(e)
                )
            ]
            result.operations.extend(operations)
        
        return result
    
    def __str__(self) -> str:
        """String representation of the cleaner."""
        return f"{self.name} v{self.version}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"{self.__class__.__name__}(name='{self.name}', version='{self.version}', enabled={self.enabled})"