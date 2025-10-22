"""
Main SDK interface for the Data Normalization SDK.

This module provides the primary SDK class that orchestrates the 
extraction, normalization, and validation pipeline.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path

from .base import (
    BaseExtractor, BaseNormalizer, BaseValidator, 
    EntityType, EntityResult, ProcessingMetadata, ProcessingError,
    ExtractionError, NormalizationError, ValidationError
)
from .schema import create_entity_result, validate_entity_schema
from .config import SDKConfig, load_config


class ExtractorRegistry:
    """Registry for managing available extractors."""
    
    def __init__(self) -> None:
        self._extractors: Dict[str, BaseExtractor] = {}
        self._entity_type_mapping: Dict[EntityType, List[str]] = {}
    
    def register(self, extractor: BaseExtractor) -> None:
        """Register an extractor.
        
        Args:
            extractor: The extractor instance to register.
        """
        name = extractor.get_name()
        self._extractors[name] = extractor
        
        # Update entity type mapping
        for entity_type in extractor.supported_entity_types:
            if entity_type not in self._entity_type_mapping:
                self._entity_type_mapping[entity_type] = []
            self._entity_type_mapping[entity_type].append(name)
    
    def get_extractors_for_entity_type(self, entity_type: EntityType) -> List[BaseExtractor]:
        """Get all extractors that support a given entity type.
        
        Args:
            entity_type: The entity type to find extractors for.
            
        Returns:
            List of extractors supporting the entity type.
        """
        extractor_names = self._entity_type_mapping.get(entity_type, [])
        return [self._extractors[name] for name in extractor_names]
    
    def get_all_extractors(self) -> List[BaseExtractor]:
        """Get all registered extractors.
        
        Returns:
            List of all registered extractors.
        """
        return list(self._extractors.values())
    
    def get_extractor(self, name: str) -> Optional[BaseExtractor]:
        """Get an extractor by name.
        
        Args:
            name: Name of the extractor.
            
        Returns:
            The extractor instance or None if not found.
        """
        return self._extractors.get(name)


class NormalizerRegistry:
    """Registry for managing available normalizers."""
    
    def __init__(self) -> None:
        self._normalizers: Dict[str, BaseNormalizer] = {}
        self._entity_type_mapping: Dict[EntityType, List[str]] = {}
    
    def register(self, normalizer: BaseNormalizer) -> None:
        """Register a normalizer.
        
        Args:
            normalizer: The normalizer instance to register.
        """
        name = normalizer.get_name()
        self._normalizers[name] = normalizer
        
        # Update entity type mapping
        for entity_type in normalizer.supported_entity_types:
            if entity_type not in self._entity_type_mapping:
                self._entity_type_mapping[entity_type] = []
            self._entity_type_mapping[entity_type].append(name)
    
    def get_normalizers_for_entity_type(self, entity_type: EntityType) -> List[BaseNormalizer]:
        """Get all normalizers that support a given entity type.
        
        Args:
            entity_type: The entity type to find normalizers for.
            
        Returns:
            List of normalizers supporting the entity type.
        """
        normalizer_names = self._entity_type_mapping.get(entity_type, [])
        return [self._normalizers[name] for name in normalizer_names]


class ValidatorRegistry:
    """Registry for managing available validators."""
    
    def __init__(self) -> None:
        self._validators: Dict[str, BaseValidator] = {}
        self._entity_type_mapping: Dict[EntityType, List[str]] = {}
    
    def register(self, validator: BaseValidator) -> None:
        """Register a validator.
        
        Args:
            validator: The validator instance to register.
        """
        name = validator.get_name()
        self._validators[name] = validator
        
        # Update entity type mapping
        for entity_type in validator.supported_entity_types:
            if entity_type not in self._entity_type_mapping:
                self._entity_type_mapping[entity_type] = []
            self._entity_type_mapping[entity_type].append(name)
    
    def get_validators_for_entity_type(self, entity_type: EntityType) -> List[BaseValidator]:
        """Get all validators that support a given entity type.
        
        Args:
            entity_type: The entity type to find validators for.
            
        Returns:
            List of validators supporting the entity type.
        """
        validator_names = self._entity_type_mapping.get(entity_type, [])
        return [self._validators[name] for name in validator_names]


class DataNormalizationSDK:
    """Main SDK interface for data extraction and normalization."""
    
    def __init__(self, config: Optional[Union[SDKConfig, str, Path]] = None) -> None:
        """Initialize the SDK.
        
        Args:
            config: Configuration for the SDK. Can be:
                - SDKConfig instance
                - Path to configuration file (string or Path)
                - None to use default configuration
        """
        # Load configuration
        if isinstance(config, SDKConfig):
            self.config = config
        elif isinstance(config, (str, Path)):
            self.config = SDKConfig.load_from_file(config)
        else:
            self.config = SDKConfig.load_default()
        
        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            raise ValueError(f"Configuration validation failed: {config_errors}")
        
        # Set up logging
        self._setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize registries
        self.extractors = ExtractorRegistry()
        self.normalizers = NormalizerRegistry()
        self.validators = ValidatorRegistry()
        
        # Load built-in components
        self._load_built_in_components()
        
        self.logger.info(f"SDK initialized with version {self.config.version}")
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.logging.level),
            format=self.config.logging.format
        )
    
    def _load_built_in_components(self) -> None:
        """Load built-in extractors, normalizers, and validators."""
        try:
            # Import and register built-in extractors
            from ..extractors.invoice import InvoiceExtractor
            from ..extractors.address import AddressExtractor
            from ..extractors.contact import ContactExtractor
            from ..extractors.product import ProductExtractor
            from ..extractors.order import OrderExtractor
            from ..extractors.log_event import LogEventExtractor
            from ..extractors.calendar_event import CalendarEventExtractor
            from ..extractors.payment import PaymentExtractor
            from ..extractors.measurement import MeasurementExtractor
            from ..extractors.people import PeopleExtractor
            
            self.register_extractor(InvoiceExtractor(getattr(self.config.extractors, 'invoice', {})))
            self.register_extractor(AddressExtractor(getattr(self.config.extractors, 'address', {})))
            self.register_extractor(ContactExtractor(getattr(self.config.extractors, 'contact', {})))
            self.register_extractor(ProductExtractor(getattr(self.config.extractors, 'product', {})))
            self.register_extractor(OrderExtractor(getattr(self.config.extractors, 'order', {})))
            self.register_extractor(LogEventExtractor(getattr(self.config.extractors, 'log_event', {})))
            self.register_extractor(CalendarEventExtractor(getattr(self.config.extractors, 'event', {})))
            self.register_extractor(PaymentExtractor(getattr(self.config.extractors, 'payment', {})))
            self.register_extractor(MeasurementExtractor(getattr(self.config.extractors, 'spec', {})))
            self.register_extractor(PeopleExtractor(getattr(self.config.extractors, 'person', {})))
            
            # Import and register built-in normalizers  
            from ..normalizers.dates import DateNormalizer
            self.register_normalizer(DateNormalizer(self.config.normalizers.dates))
            
            # Import and register built-in validators
            from ..validators.schema import SchemaValidator
            self.register_validator(SchemaValidator())
            
            self.logger.debug("Built-in components loaded successfully")
            
        except ImportError as e:
            self.logger.warning(f"Could not load some built-in components: {e}")
        except Exception as e:
            self.logger.error(f"Error loading built-in components: {e}")
    
    def process(self, text: str, entity_type: Optional[EntityType] = None) -> EntityResult:
        """Process text through the complete extraction, normalization, and validation pipeline.
        
        Args:
            text: Input text to process.
            entity_type: Optional specific entity type to process as. 
                        If None, will auto-detect the most likely entity type.
        
        Returns:
            EntityResult containing the processed data.
            
        Raises:
            ProcessingError: If processing fails at any stage.
            ValueError: If input text is invalid or too long.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        
        if len(text) > self.config.performance.max_text_length:
            raise ValueError(
                f"Input text too long ({len(text)} characters). "
                f"Maximum allowed: {self.config.performance.max_text_length}"
            )
        
        text = text.strip()
        
        self.logger.debug(f"Processing text: {text[:100]}...")
        
        # Stage 1: Extraction
        extracted_data, extraction_confidence, detected_entity_type = self._extract_data(text, entity_type)
        
        # Stage 2: Normalization  
        normalized_data, processing_metadata = self._normalize_data(
            extracted_data, detected_entity_type, extraction_confidence
        )
        
        # Stage 3: Validation
        entity_result = create_entity_result(
            entity_type=detected_entity_type,
            attributes=normalized_data,
            confidence=processing_metadata.confidence,
            transformations=processing_metadata.transformations,
            **{k: v for k, v in processing_metadata.__dict__.items() 
               if k not in ['confidence', 'transformations']}
        )
        
        validation_result = self._validate_result(entity_result)
        
        self.logger.info(
            f"Processing complete. Entity: {detected_entity_type.value}, "
            f"Confidence: {entity_result.metadata.confidence:.3f}"
        )
        
        return entity_result
    
    def _extract_data(self, text: str, target_entity_type: Optional[EntityType] = None) -> Tuple[Dict[str, Any], float, EntityType]:
        """Extract data from text using appropriate extractors.
        
        Args:
            text: Input text to extract data from.
            target_entity_type: Optional target entity type.
            
        Returns:
            Tuple of (extracted_data, confidence, detected_entity_type)
            
        Raises:
            ExtractionError: If extraction fails or no suitable extractor found.
        """
        self.logger.debug("Starting extraction stage")
        
        if target_entity_type is not None:
            # Use extractors for specific entity type
            extractors = self.extractors.get_extractors_for_entity_type(target_entity_type)
            if not extractors:
                raise ExtractionError(f"No extractors available for entity type: {target_entity_type}")
        else:
            # Try all extractors and find the best match
            extractors = self.extractors.get_all_extractors()
            if not extractors:
                raise ExtractionError("No extractors are available")
        
        best_result = None
        best_confidence = 0.0
        best_entity_type = None
        
        for extractor in extractors:
            try:
                # Check if this extractor can handle the text
                can_extract, detection_confidence = extractor.can_extract(text)
                
                if not can_extract:
                    continue
                
                # Extract data
                extracted_data, extraction_confidence = extractor.extract(text)
                
                # Overall confidence is combination of detection and extraction
                overall_confidence = (detection_confidence + extraction_confidence) / 2.0
                
                if overall_confidence > best_confidence:
                    best_result = extracted_data
                    best_confidence = overall_confidence
                    # Get the most likely entity type from this extractor
                    best_entity_type = list(extractor.supported_entity_types)[0]
                
            except Exception as e:
                self.logger.warning(f"Extractor {extractor.get_name()} failed: {e}")
                continue
        
        if best_result is None:
            raise ExtractionError("No extractor could successfully process the input text")
        
        if best_confidence < self.config.confidence.extraction_threshold:
            self.logger.warning(
                f"Extraction confidence ({best_confidence:.3f}) below threshold "
                f"({self.config.confidence.extraction_threshold})"
            )
        
        self.logger.debug(f"Extraction complete. Best entity type: {best_entity_type}, confidence: {best_confidence:.3f}")
        
        return best_result, best_confidence, best_entity_type or EntityType.INVOICE  # fallback
    
    def _normalize_data(self, extracted_data: Dict[str, Any], entity_type: EntityType, extraction_confidence: float) -> Tuple[Dict[str, Any], ProcessingMetadata]:
        """Normalize extracted data using appropriate normalizers.
        
        Args:
            extracted_data: Raw extracted data.
            entity_type: Detected entity type.
            extraction_confidence: Confidence from extraction stage.
            
        Returns:
            Tuple of (normalized_data, processing_metadata)
        """
        self.logger.debug("Starting normalization stage")
        
        normalizers = self.normalizers.get_normalizers_for_entity_type(entity_type)
        
        if not normalizers:
            # No specific normalizers, return data as-is with basic metadata
            self.logger.debug("No normalizers available, returning raw data")
            metadata = ProcessingMetadata(
                confidence=extraction_confidence,
                transformations=["extraction_only"],
                source="extraction"
            )
            return extracted_data, metadata
        
        # Apply normalizers in sequence
        current_data = extracted_data.copy()
        all_transformations = ["extraction"]
        
        for normalizer in normalizers:
            try:
                normalized_data, norm_metadata = normalizer.normalize(current_data, entity_type)
                current_data = normalized_data
                all_transformations.extend(norm_metadata.transformations)
                
                self.logger.debug(f"Applied normalizer {normalizer.get_name()}")
                
            except Exception as e:
                self.logger.warning(f"Normalizer {normalizer.get_name()} failed: {e}")
                # Continue with current data
                continue
        
        # Create final metadata
        final_metadata = ProcessingMetadata(
            confidence=extraction_confidence,  # Will be updated based on normalization success
            transformations=all_transformations,
            source="extraction+normalization"
        )
        
        self.logger.debug("Normalization complete")
        
        return current_data, final_metadata
    
    def _validate_result(self, entity_result: EntityResult) -> Tuple[bool, List[str], float]:
        """Validate the final entity result.
        
        Args:
            entity_result: Complete entity result to validate.
            
        Returns:
            Tuple of (is_valid, validation_errors, confidence)
        """
        self.logger.debug("Starting validation stage")
        
        all_errors: List[str] = []
        validation_confidences: List[float] = []
        
        # Schema validation first
        schema_errors = validate_entity_schema(entity_result)
        all_errors.extend(schema_errors)
        
        # Apply registered validators
        validators = self.validators.get_validators_for_entity_type(entity_result.entity_type)
        
        for validator in validators:
            try:
                is_valid, errors, confidence = validator.validate(entity_result)
                all_errors.extend(errors)
                validation_confidences.append(confidence)
                
                self.logger.debug(f"Validator {validator.get_name()}: valid={is_valid}, confidence={confidence:.3f}")
                
            except Exception as e:
                self.logger.warning(f"Validator {validator.get_name()} failed: {e}")
                continue
        
        # Calculate overall validation confidence
        if validation_confidences:
            avg_validation_confidence = sum(validation_confidences) / len(validation_confidences)
        else:
            avg_validation_confidence = 1.0 if not all_errors else 0.5
        
        is_valid = len(all_errors) == 0
        
        # Update entity metadata with validation results
        if not is_valid:
            entity_result.metadata.transformations.append("validation_warnings")
        
        self.logger.debug(f"Validation complete. Valid: {is_valid}, confidence: {avg_validation_confidence:.3f}")
        
        return is_valid, all_errors, avg_validation_confidence
    
    def get_supported_entity_types(self) -> Set[EntityType]:
        """Get all entity types supported by registered extractors.
        
        Returns:
            Set of supported EntityType values.
        """
        supported_types = set()
        for extractor in self.extractors.get_all_extractors():
            supported_types.update(extractor.supported_entity_types)
        return supported_types
    
    def register_extractor(self, extractor: BaseExtractor) -> None:
        """Register a custom extractor.
        
        Args:
            extractor: The extractor instance to register.
        """
        self.extractors.register(extractor)
        self.logger.info(f"Registered extractor: {extractor.get_name()}")
    
    def register_normalizer(self, normalizer: BaseNormalizer) -> None:
        """Register a custom normalizer.
        
        Args:
            normalizer: The normalizer instance to register.
        """
        self.normalizers.register(normalizer)
        self.logger.info(f"Registered normalizer: {normalizer.get_name()}")
    
    def register_validator(self, validator: BaseValidator) -> None:
        """Register a custom validator.
        
        Args:
            validator: The validator instance to register.
        """
        self.validators.register(validator)
        self.logger.info(f"Registered validator: {validator.get_name()}")