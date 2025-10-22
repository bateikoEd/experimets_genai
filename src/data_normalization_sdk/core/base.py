"""
Base classes for the Data Normalization SDK.

This module provides abstract base classes that define the interfaces
for extractors, normalizers, and validators in the SDK pipeline.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class EntityType(Enum):
    """Supported entity types for data extraction and normalization."""
    
    INVOICE = "invoice"
    ADDRESS = "address"
    CONTACT = "contact"
    PRODUCT = "product"
    ORDER = "order"
    LOG_EVENT = "log_event"
    EVENT = "event"
    PAYMENT = "payment"
    SPEC = "spec"  # measurements/specifications
    PERSON = "person"


@dataclass
class ProcessingMetadata:
    """Metadata tracking for processing stages and confidence scoring."""
    
    confidence: float  # 0.0 to 1.0
    transformations: List[str]
    source: Optional[str] = None
    locale_hint: Optional[str] = None
    parser_version: Optional[str] = None
    normalization_ruleset: Optional[str] = None
    standard: Optional[str] = None
    heuristics: Optional[List[str]] = None
    tokenization: Optional[str] = None
    locale_detected: Optional[str] = None
    schema: Optional[str] = None
    timezone_source: Optional[str] = None
    tz_resolution: Optional[str] = None
    range_delimiter: Optional[str] = None
    minor_unit_exponent: Optional[int] = None
    conversions: Optional[Dict[str, float]] = None
    precision: Optional[int] = None
    phone_rules: Optional[str] = None
    transliteration: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate confidence score is within valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass
class EntityResult:
    """Unified result structure for all entity types."""
    
    entity_type: EntityType
    attributes: Dict[str, Any]
    metadata: ProcessingMetadata
    
    def __post_init__(self) -> None:
        """Validate entity result structure."""
        if not isinstance(self.entity_type, EntityType):
            raise TypeError(f"entity_type must be EntityType enum, got {type(self.entity_type)}")
        if not isinstance(self.attributes, dict):
            raise TypeError(f"attributes must be dict, got {type(self.attributes)}")
        if not isinstance(self.metadata, ProcessingMetadata):
            raise TypeError(f"metadata must be ProcessingMetadata, got {type(self.metadata)}")


class BaseExtractor(ABC):
    """Abstract base class for domain-specific data extractors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize extractor with optional configuration.
        
        Args:
            config: Optional configuration dictionary for customizing extraction behavior.
        """
        self.config = config or {}
        self._confidence_threshold = self.config.get('confidence_threshold', 0.5)
    
    @property
    @abstractmethod
    def supported_entity_types(self) -> Set[EntityType]:
        """Return the set of entity types this extractor can handle."""
        pass
    
    @abstractmethod
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract structured data from text.
        
        Args:
            text: Input text to extract data from.
            
        Returns:
            Tuple of (extracted_data, confidence_score)
            - extracted_data: Dictionary containing extracted fields
            - confidence_score: Float between 0.0 and 1.0 indicating extraction confidence
        """
        pass
    
    def can_extract(self, text: str) -> Tuple[bool, float]:
        """Determine if this extractor can process the given text.
        
        Args:
            text: Input text to evaluate.
            
        Returns:
            Tuple of (can_extract, confidence) where:
            - can_extract: Boolean indicating if extraction is likely to succeed
            - confidence: Float between 0.0 and 1.0 indicating detection confidence
        """
        try:
            _, confidence = self.extract(text)
            return confidence >= self._confidence_threshold, confidence
        except Exception:
            return False, 0.0
    
    @abstractmethod
    def get_name(self) -> str:
        """Return a unique name for this extractor."""
        pass


class BaseNormalizer(ABC):
    """Abstract base class for data normalizers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize normalizer with optional configuration.
        
        Args:
            config: Optional configuration dictionary for customizing normalization behavior.
        """
        self.config = config or {}
    
    @property
    @abstractmethod
    def supported_entity_types(self) -> Set[EntityType]:
        """Return the set of entity types this normalizer can handle."""
        pass
    
    @abstractmethod
    def normalize(self, extracted_data: Dict[str, Any], entity_type: EntityType) -> Tuple[Dict[str, Any], ProcessingMetadata]:
        """Normalize extracted data to standard formats.
        
        Args:
            extracted_data: Raw extracted data from an extractor.
            entity_type: The type of entity being normalized.
            
        Returns:
            Tuple of (normalized_data, metadata) where:
            - normalized_data: Dictionary with standardized field values
            - metadata: ProcessingMetadata with normalization details and confidence
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return a unique name for this normalizer."""
        pass


class BaseValidator(ABC):
    """Abstract base class for data validators."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize validator with optional configuration.
        
        Args:
            config: Optional configuration dictionary for customizing validation behavior.
        """
        self.config = config or {}
    
    @property
    @abstractmethod
    def supported_entity_types(self) -> Set[EntityType]:
        """Return the set of entity types this validator can handle."""
        pass
    
    @abstractmethod
    def validate(self, entity_result: EntityResult) -> Tuple[bool, List[str], float]:
        """Validate an entity result for correctness and completeness.
        
        Args:
            entity_result: Complete entity result to validate.
            
        Returns:
            Tuple of (is_valid, validation_errors, confidence) where:
            - is_valid: Boolean indicating if validation passed
            - validation_errors: List of validation error messages (empty if valid)
            - confidence: Float between 0.0 and 1.0 indicating validation confidence
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return a unique name for this validator."""
        pass


class ProcessingError(Exception):
    """Base exception for processing errors in the SDK."""
    
    def __init__(self, message: str, stage: str, original_error: Optional[Exception] = None) -> None:
        """Initialize processing error.
        
        Args:
            message: Human-readable error message.
            stage: Processing stage where error occurred (extract/normalize/validate).
            original_error: Original exception that caused this error (if any).
        """
        super().__init__(message)
        self.stage = stage
        self.original_error = original_error


class ExtractionError(ProcessingError):
    """Exception raised during data extraction."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None) -> None:
        super().__init__(message, "extraction", original_error)


class NormalizationError(ProcessingError):
    """Exception raised during data normalization."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None) -> None:
        super().__init__(message, "normalization", original_error)


class ValidationError(ProcessingError):
    """Exception raised during data validation."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None) -> None:
        super().__init__(message, "validation", original_error)