"""
Cleaning pipeline for orchestrating multiple cleaning operations.
"""

import time
from typing import Any, Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from .base import BaseCleaner, CleaningContext, CleanResult, CleaningStats
from .registry import CleaningPluginRegistry
from .config import CleaningConfig, ConfigManager
from ..core import EntityType


class CleaningPipeline:
    """Orchestrates multiple cleaning operations in sequence."""
    
    def __init__(self, cleaners: List[BaseCleaner] = None,
                 max_workers: int = 1,
                 enable_parallel: bool = False,
                 fail_fast: bool = False,
                 config: Optional[CleaningConfig] = None,
                 config_name: Optional[str] = None):
        """
        Initialize the cleaning pipeline.
        
        Args:
            cleaners: List of cleaners to apply
            max_workers: Maximum number of parallel workers
            enable_parallel: Whether to enable parallel processing
            fail_fast: Whether to stop on first failure
            config: Cleaning configuration to use
            config_name: Name of configuration to load from config manager
        """
        self.cleaners = cleaners or []
        self.max_workers = max_workers
        self.enable_parallel = enable_parallel
        self.fail_fast = fail_fast
        self.context = CleaningContext()
        self._lock = Lock()
        self._stats = CleaningStats()
        
        # Configuration management
        self.config_manager = ConfigManager()
        self.config = config or (self.config_manager.get_config(config_name) if config_name else CleaningConfig())
        
        # Apply configuration
        self._apply_config()
    
    def _apply_config(self):
        """Apply configuration to the pipeline."""
        # Set global settings
        self.enable_parallel = self.config.enabled and self.enable_parallel
        self.fail_fast = self.config.skip_on_error
        
        # Configure cleaners based on pipeline order
        registry = CleaningPluginRegistry()
        
        # Create cleaners ONLY in the specified order
        ordered_cleaners = []
        for cleaner_name in self.config.pipeline_order:
            cleaner = registry.get_plugin(cleaner_name)
            if cleaner:
                # Apply configuration if available
                cleaner_config = self.config.get_cleaner_config(cleaner_name)
                if cleaner_config:
                    cleaner.configure(**cleaner_config)
                ordered_cleaners.append(cleaner)
            else:
                print(f"Warning: Cleaner '{cleaner_name}' not found in registry")
        
        self.cleaners = ordered_cleaners
    
    def add_cleaner(self, cleaner: BaseCleaner):
        """Add a cleaner to the pipeline."""
        self.cleaners.append(cleaner)
    
    def remove_cleaner(self, cleaner_name: str):
        """Remove a cleaner from the pipeline by name."""
        self.cleaners = [c for c in self.cleaners if c.name != cleaner_name]
    
    def get_cleaner(self, cleaner_name: str) -> Optional[BaseCleaner]:
        """Get a cleaner by name."""
        for cleaner in self.cleaners:
            if cleaner.name == cleaner_name:
                return cleaner
        return None
    
    def set_cleaners(self, cleaners: List[BaseCleaner]):
        """Set the list of cleaners for the pipeline."""
        self.cleaners = cleaners
    
    def configure_cleaner(self, cleaner_name: str, **kwargs):
        """Configure a specific cleaner in the pipeline."""
        cleaner = self.get_cleaner(cleaner_name)
        if cleaner:
            cleaner.configure(**kwargs)
    
    def enable_cleaner(self, cleaner_name: str, enabled: bool = True):
        """Enable or disable a specific cleaner."""
        cleaner = self.get_cleaner(cleaner_name)
        if cleaner:
            cleaner.enabled = enabled
    
    def process(self, data: Any, entity_type: Optional[EntityType] = None,
                context: Optional[CleaningContext] = None) -> CleanResult:
        """
        Process data through the cleaning pipeline.
        
        Args:
            data: Input data to clean
            entity_type: Type of entity being processed
            context: Optional cleaning context
            
        Returns:
            CleanResult containing cleaned data and operation details
        """
        start_time = time.time()
        
        # Create or use provided context
        if context is None:
            context = CleaningContext(entity_type)
        else:
            context.entity_type = entity_type or context.entity_type
        
        # Set input data in context
        context.set_input_data(data)
        
        # Apply entity-specific configuration if available
        if entity_type:
            entity_type_str = entity_type.value if hasattr(entity_type, 'value') else entity_type
            entity_config = self.config.get_entity_config(entity_type_str)
            if entity_config:
                # Update pipeline configuration for this entity type
                original_config = self.config.to_dict()
                # Only update allowed config fields
                allowed_fields = ['pipeline_order', 'max_operations', 'min_confidence']
                filtered_entity_config = {k: v for k, v in entity_config.items() if k in allowed_fields}
                self.config = CleaningConfig.from_dict({**original_config, **filtered_entity_config})
                self._apply_config()
        
        # Filter enabled cleaners
        enabled_cleaners = [c for c in self.cleaners if c.enabled]
        
        if not enabled_cleaners:
            # No cleaners enabled, return original data
            result = CleanResult(data, [], context)
            result.stats.processing_time_ms = (time.time() - start_time) * 1000
            return result
        
        # Process through cleaners
        if self.enable_parallel and len(enabled_cleaners) > 1 and self.max_workers > 1:
            result = self._process_parallel(data, enabled_cleaners, context)
        else:
            result = self._process_sequential(data, enabled_cleaners, context)
        
        # Set processing time
        result.stats.processing_time_ms = (time.time() - start_time) * 1000
        
        # Merge stats into main context
        context.stats.merge(result.stats)
        
        return result
    
    def _process_sequential(self, data: Any, cleaners: List[BaseCleaner], 
                           context: CleaningContext) -> CleanResult:
        """Process data sequentially through cleaners."""
        current_data = data
        all_operations = []
        
        for i, cleaner in enumerate(cleaners):
            # Create child context for this cleaner
            cleaner_context = context.create_child_context()
            
            try:
                # Process through cleaner
                result = cleaner.clean(current_data, cleaner_context)
                
                # Collect operations
                all_operations.extend(result.operations)
                
                # Update current data
                current_data = result.cleaned_data
                
                # If failed fast and this cleaner failed, stop processing
                if self.fail_fast and not result.success:
                    break
                    
            except Exception as e:
                # Create error operation
                error_op = self._create_error_operation(
                    cleaner.name, "sequential_processing", str(e)
                )
                all_operations.append(error_op)
                
                if self.fail_fast:
                    break
        
        return CleanResult(current_data, all_operations, context)
    
    def _process_parallel(self, data: Any, cleaners: List[BaseCleaner], 
                         context: CleaningContext) -> CleanResult:
        """Process data in parallel through cleaners."""
        all_operations = []
        results = {}
        
        def process_cleaner(cleaner: BaseCleaner) -> tuple:
            """Process a single cleaner."""
            cleaner_context = context.create_child_context()
            try:
                result = cleaner.clean(data, cleaner_context)
                return cleaner.name, result
            except Exception as e:
                error_op = self._create_error_operation(
                    cleaner.name, "parallel_processing", str(e)
                )
                error_result = CleanResult(data, [error_op], cleaner_context)
                return cleaner.name, error_result
        
        # Process cleaners in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_cleaner = {
                executor.submit(process_cleaner, cleaner): cleaner 
                for cleaner in cleaners
            }
            
            # Collect results
            for future in as_completed(future_to_cleaner):
                cleaner_name = future_to_cleaner[future]
                try:
                    name, result = future.result()
                    results[name] = result
                    all_operations.extend(result.operations)
                except Exception as e:
                    error_op = self._create_error_operation(
                        cleaner_name.name, "parallel_execution", str(e)
                    )
                    all_operations.append(error_op)
        
        # Merge results (last writer wins for conflicts)
        final_data = data
        for cleaner_name, result in results.items():
            if result.success:
                final_data = result.cleaned_data
        
        return CleanResult(final_data, all_operations, context)
    
    def _create_error_operation(self, cleaner_name: str, operation_type: str, 
                               error_message: str):
        """Create an error operation."""
        from .base import CleaningOperation, CleaningOperationType
        
        return CleaningOperation(
            field=cleaner_name,
            operation_type=CleaningOperationType.VALIDATE,
            description=f"Error in {cleaner_name}: {operation_type}",
            success=False,
            error_message=error_message
        )
    
    def get_stats(self) -> CleaningStats:
        """Get overall pipeline statistics."""
        return self._stats
    
    def reset_stats(self):
        """Reset pipeline statistics."""
        self._stats = CleaningStats()
    
    def validate_pipeline(self) -> List[str]:
        """
        Validate the pipeline configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for duplicate cleaner names
        cleaner_names = [c.name for c in self.cleaners]
        duplicates = set(name for name in cleaner_names if cleaner_names.count(name) > 1)
        if duplicates:
            errors.append(f"Duplicate cleaner names: {', '.join(duplicates)}")
        
        # Validate each cleaner
        for cleaner in self.cleaners:
            cleaner_errors = cleaner.validate_config()
            if cleaner_errors:
                errors.extend(f"{cleaner.name}: {error}" for error in cleaner_errors)
        
        return errors
    
    def get_cleaner_info(self) -> List[Dict[str, Any]]:
        """Get information about all cleaners in the pipeline."""
        return [
            {
                "name": cleaner.name,
                "version": cleaner.version,
                "enabled": cleaner.enabled,
                "config": cleaner.config
            }
            for cleaner in self.cleaners
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline to dictionary representation."""
        return {
            "cleaners": self.get_cleaner_info(),
            "max_workers": self.max_workers,
            "enable_parallel": self.enable_parallel,
            "fail_fast": self.fail_fast,
            "stats": self._stats.to_dict()
        }
    
    def __len__(self) -> int:
        """Get number of cleaners in pipeline."""
        return len(self.cleaners)
    
    def __bool__(self) -> bool:
        """Check if pipeline has any cleaners."""
        return len(self.cleaners) > 0
    
    def __str__(self) -> str:
        """String representation of the pipeline."""
        cleaner_names = [c.name for c in self.cleaners if c.enabled]
        return f"CleaningPipeline(cleaners={len(cleaner_names)}, parallel={self.enable_parallel})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"CleaningPipeline(cleaners={len(self.cleaners)}, "
                f"enabled={len([c for c in self.cleaners if c.enabled])}, "
                f"max_workers={self.max_workers}, parallel={self.enable_parallel})")
    
    def set_config(self, config: CleaningConfig):
        """Set a new configuration for the pipeline."""
        self.config = config
        self._apply_config()
    
    def load_config(self, config_name: str):
        """Load a configuration by name."""
        self.config = self.config_manager.get_config(config_name)
        self._apply_config()
    
    def save_config(self, name: str, format: str = 'json'):
        """Save the current configuration."""
        self.config_manager.save_config(name, self.config, format)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            "enabled": self.config.enabled,
            "pipeline_order": self.config.pipeline_order,
            "cleaner_count": len(self.cleaners),
            "enabled_cleaners": len([c for c in self.cleaners if c.enabled]),
            "entity_configs": list(self.config.entity_configs.keys()),
            "max_operations": self.config.max_operations,
            "min_confidence": self.config.min_confidence
        }
    
    def update_cleaner_config(self, cleaner_name: str, config_dict: Dict[str, Any]):
        """Update configuration for a specific cleaner."""
        current_config = self.config.get_cleaner_config(cleaner_name)
        current_config.update(config_dict)
        self.config.set_cleaner_config(cleaner_name, current_config)
        
        # Reapply configuration to update the cleaner
        self._apply_config()
    
    def update_entity_config(self, entity_type: str, config_dict: Dict[str, Any]):
        """Update configuration for a specific entity type."""
        current_config = self.config.get_entity_config(entity_type)
        current_config.update(config_dict)
        self.config.set_entity_config(entity_type, current_config)
    
    def process_batch(self, batch_data: List[Dict[str, Any]], entity_type: Optional[EntityType] = None) -> List[CleanResult]:
        """Process multiple items in batch."""
        results = []
        
        for item in batch_data:
            try:
                item_entity_type_str = item.get('entity_type')
                item_entity_type = EntityType(item_entity_type_str) if item_entity_type_str else entity_type
                
                # Process the entire item, not just the text field
                result = self.process(item, item_entity_type)
                results.append(result)
            except Exception as e:
                # Create a failed result for this item
                failed_result = CleanResult(
                    cleaned_data=item,
                    operations=[],
                    context=CleaningContext()
                )
                failed_result.operations.append(
                    CleaningOperation(
                        field="batch_processing",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Batch processing failed: {str(e)}",
                        success=False,
                        error_message=str(e)
                    )
                )
                results.append(failed_result)
        
        return results


class ConditionalCleaningPipeline(CleaningPipeline):
    """Pipeline that applies cleaners conditionally based on data characteristics."""
    
    def __init__(self, cleaners: List[BaseCleaner] = None, 
                 condition_func: Optional[Callable[[Any, CleaningContext], bool]] = None,
                 **kwargs):
        """
        Initialize conditional cleaning pipeline.
        
        Args:
            cleaners: List of cleaners to apply
            condition_func: Function that determines if cleaning should be applied
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(cleaners, **kwargs)
        self.condition_func = condition_func or self._default_condition
    
    def _default_condition(self, data: Any, context: CleaningContext) -> bool:
        """Default condition: always apply cleaning."""
        return True
    
    def process(self, data: Any, entity_type: Optional[EntityType] = None, 
                context: Optional[CleaningContext] = None) -> CleanResult:
        """
        Process data through the cleaning pipeline if condition is met.
        
        Args:
            data: Input data to clean
            entity_type: Type of entity being processed
            context: Optional cleaning context
            
        Returns:
            CleanResult containing cleaned data and operation details
        """
        # Create or use provided context
        if context is None:
            context = CleaningContext(entity_type)
        else:
            context.entity_type = entity_type or context.entity_type
        
        # Check if cleaning should be applied
        if not self.condition_func(data, context):
            # Return original data with no operations
            result = CleanResult(data, [], context)
            result.stats.processing_time_ms = 0.0
            return result
        
        # Apply parent processing
        return super().process(data, entity_type, context)
    
    def set_condition(self, condition_func: Callable[[Any, CleaningContext], bool]):
        """Set the condition function."""
        self.condition_func = condition_func


class BatchCleaningPipeline:
    """Pipeline for processing batches of data with cleaning."""
    
    def __init__(self, pipeline: CleaningPipeline, batch_size: int = 100,
                 progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        Initialize batch cleaning pipeline.
        
        Args:
            pipeline: Cleaning pipeline to apply to each batch
            batch_size: Size of each batch
            progress_callback: Optional callback for progress updates
        """
        self.pipeline = pipeline
        self.batch_size = batch_size
        self.progress_callback = progress_callback
    
    def process_batch(self, data_list: List[Any], 
                     entity_type: Optional[EntityType] = None,
                     context: Optional[CleaningContext] = None) -> List[CleanResult]:
        """
        Process a batch of data through the cleaning pipeline.
        
        Args:
            data_list: List of input data to clean
            entity_type: Type of entity being processed
            context: Optional cleaning context
            
        Returns:
            List of CleanResult objects
        """
        results = []
        total_items = len(data_list)
        
        for i in range(0, total_items, self.batch_size):
            batch_end = min(i + self.batch_size, total_items)
            batch = data_list[i:batch_end]
            
            # Process each item in the batch
            batch_results = []
            for item in batch:
                result = self.pipeline.process(item, entity_type, context)
                batch_results.append(result)
            
            results.extend(batch_results)
            
            # Update progress
            if self.progress_callback:
                self.progress_callback(batch_end, total_items)
        
        return results
    
    def process_parallel_batch(self, data_list: List[Any], 
                              entity_type: Optional[EntityType] = None,
                              context: Optional[CleaningContext] = None,
                              max_workers: int = 4) -> List[CleanResult]:
        """
        Process a batch of data in parallel.
        
        Args:
            data_list: List of input data to clean
            entity_type: Type of entity being processed
            context: Optional cleaning context
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of CleanResult objects
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = [None] * len(data_list)
        total_items = len(data_list)
        
        def process_item(index: int, item: Any):
            """Process a single item."""
            result = self.pipeline.process(item, entity_type, context)
            return index, result
        
        # Process items in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(process_item, i, item): i 
                for i, item in enumerate(data_list)
            }
            
            # Collect results
            completed = 0
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    idx, result = future.result()
                    results[idx] = result
                    completed += 1
                    
                    # Update progress
                    if self.progress_callback and completed % 10 == 0:
                        self.progress_callback(completed, total_items)
                        
                except Exception as e:
                    # Create error result
                    error_result = CleanResult(
                        data_list[index],
                        [],
                        context or CleaningContext(entity_type)
                    )
                    error_result.stats.operations.append(
                        self.pipeline._create_error_operation(
                            "batch_processing", "parallel_execution", str(e)
                        )
                    )
                    results[index] = error_result
        
        return results
    
    def process_batch(self, data_list: List[Any],
                     entity_type: Optional[EntityType] = None,
                     context: Optional[CleaningContext] = None) -> List[CleanResult]:
        """
        Process a batch of data through the cleaning pipeline.
        
        Args:
            data_list: List of input data to clean
            entity_type: Type of entity being processed
            context: Optional cleaning context
            
        Returns:
            List of CleanResult objects
        """
        results = []
        
        for data in data_list:
            result = self.process(data, entity_type, context)
            results.append(result)
        
        return results