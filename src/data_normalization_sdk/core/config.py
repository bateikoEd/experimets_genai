"""
Configuration management for the Data Normalization SDK.

This module provides configuration loading, validation, and management
functionality for customizing SDK behavior.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


@dataclass
class ConfidenceConfig:
    """Configuration for confidence thresholds."""
    
    extraction_threshold: float = 0.6
    normalization_threshold: float = 0.7
    entity_threshold: float = 0.8
    entity_specific: Dict[str, float] = field(default_factory=dict)


@dataclass
class ExtractorConfig:
    """Configuration for data extractors."""
    
    enabled: Dict[str, bool] = field(default_factory=dict)
    invoice: Dict[str, Any] = field(default_factory=dict)
    address: Dict[str, Any] = field(default_factory=dict)
    contact: Dict[str, Any] = field(default_factory=dict)
    log_event: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizerConfig:
    """Configuration for data normalizers."""
    
    dates: Dict[str, Any] = field(default_factory=dict)
    currencies: Dict[str, Any] = field(default_factory=dict)
    phones: Dict[str, Any] = field(default_factory=dict)
    addresses: Dict[str, Any] = field(default_factory=dict)
    text: Dict[str, Any] = field(default_factory=dict)


@dataclass  
class ValidatorConfig:
    """Configuration for data validators."""
    
    schema: Dict[str, Any] = field(default_factory=dict)
    standards: Dict[str, Any] = field(default_factory=dict)
    cross_field: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_extracted_data: bool = False
    log_normalized_data: bool = False
    log_processing_times: bool = True
    log_confidence_scores: bool = True


@dataclass
class PerformanceConfig:
    """Configuration for performance settings."""
    
    cache_patterns: bool = True
    max_text_length: int = 10000
    processing_timeout: float = 30.0


@dataclass
class SDKConfig:
    """Main configuration class for the Data Normalization SDK."""
    
    version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    confidence: ConfidenceConfig = field(default_factory=ConfidenceConfig)
    extractors: ExtractorConfig = field(default_factory=ExtractorConfig)
    normalizers: NormalizerConfig = field(default_factory=NormalizerConfig)
    validators: ValidatorConfig = field(default_factory=ValidatorConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    @classmethod
    def load_from_file(cls, config_path: Union[str, Path]) -> "SDKConfig":
        """Load configuration from a YAML file.
        
        Args:
            config_path: Path to the YAML configuration file.
            
        Returns:
            SDKConfig instance loaded from the file.
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            yaml.YAMLError: If the YAML file is malformed.
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
            
        return cls.from_dict(config_data)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SDKConfig":
        """Create SDKConfig from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration data.
            
        Returns:
            SDKConfig instance created from the dictionary.
        """
        # Extract top-level SDK settings
        sdk_section = config_dict.get('sdk', {})
        
        return cls(
            version=sdk_section.get('version', '0.1.0'),
            debug=sdk_section.get('debug', False),
            log_level=sdk_section.get('log_level', 'INFO'),
            
            confidence=ConfidenceConfig(
                **config_dict.get('confidence', {})
            ),
            
            extractors=ExtractorConfig(
                **config_dict.get('extractors', {})
            ),
            
            normalizers=NormalizerConfig(
                **config_dict.get('normalizers', {})
            ),
            
            validators=ValidatorConfig(
                **config_dict.get('validators', {})
            ),
            
            logging=LoggingConfig(
                **config_dict.get('logging', {})
            ),
            
            performance=PerformanceConfig(
                **config_dict.get('performance', {})
            )
        )
    
    @classmethod
    def load_default(cls) -> "SDKConfig":
        """Load the default configuration.
        
        Returns:
            SDKConfig instance with default settings.
        """
        # Get path to default config file
        config_dir = Path(__file__).parent
        default_config_path = config_dir / "default.yaml"
        
        if default_config_path.exists():
            return cls.load_from_file(default_config_path)
        else:
            # Fallback to hardcoded defaults if file missing
            return cls()
    
    def merge_with(self, other_config: Union["SDKConfig", Dict[str, Any]]) -> "SDKConfig":
        """Merge this configuration with another configuration.
        
        Args:
            other_config: Another SDKConfig instance or configuration dictionary.
            
        Returns:
            New SDKConfig instance with merged settings.
        """
        if isinstance(other_config, dict):
            other_config = self.from_dict(other_config)
            
        # Create new config by copying current values and updating with other
        merged_dict = self.to_dict()
        other_dict = other_config.to_dict()
        
        # Deep merge dictionaries
        def deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = deep_merge(base[key], value)
                else:
                    base[key] = value
            return base
        
        merged_dict = deep_merge(merged_dict, other_dict)
        return self.from_dict(merged_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format.
        
        Returns:
            Dictionary representation of the configuration.
        """
        return {
            'sdk': {
                'version': self.version,
                'debug': self.debug,
                'log_level': self.log_level
            },
            'confidence': {
                'extraction_threshold': self.confidence.extraction_threshold,
                'normalization_threshold': self.confidence.normalization_threshold,
                'entity_threshold': self.confidence.entity_threshold,
                'entity_specific': self.confidence.entity_specific
            },
            'extractors': {
                'enabled': self.extractors.enabled,
                'invoice': self.extractors.invoice,
                'address': self.extractors.address,
                'contact': self.extractors.contact,
                'log_event': self.extractors.log_event
            },
            'normalizers': {
                'dates': self.normalizers.dates,
                'currencies': self.normalizers.currencies,
                'phones': self.normalizers.phones,
                'addresses': self.normalizers.addresses,
                'text': self.normalizers.text
            },
            'validators': {
                'schema': self.validators.schema,
                'standards': self.validators.standards,
                'cross_field': self.validators.cross_field
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'log_extracted_data': self.logging.log_extracted_data,
                'log_normalized_data': self.logging.log_normalized_data,
                'log_processing_times': self.logging.log_processing_times,
                'log_confidence_scores': self.logging.log_confidence_scores
            },
            'performance': {
                'cache_patterns': self.performance.cache_patterns,
                'max_text_length': self.performance.max_text_length,
                'processing_timeout': self.performance.processing_timeout
            }
        }
    
    def get_entity_confidence_threshold(self, entity_type: str) -> float:
        """Get the confidence threshold for a specific entity type.
        
        Args:
            entity_type: The entity type to get threshold for.
            
        Returns:
            Confidence threshold for the entity type.
        """
        return self.confidence.entity_specific.get(
            entity_type, 
            self.confidence.entity_threshold
        )
    
    def is_extractor_enabled(self, extractor_name: str) -> bool:
        """Check if a specific extractor is enabled.
        
        Args:
            extractor_name: Name of the extractor to check.
            
        Returns:
            True if extractor is enabled, False otherwise.
        """
        return self.extractors.enabled.get(extractor_name, True)
    
    def validate(self) -> List[str]:
        """Validate the configuration for correctness.
        
        Returns:
            List of validation errors. Empty if configuration is valid.
        """
        errors: List[str] = []
        
        # Validate confidence thresholds
        if not 0.0 <= self.confidence.extraction_threshold <= 1.0:
            errors.append("extraction_threshold must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence.normalization_threshold <= 1.0:
            errors.append("normalization_threshold must be between 0.0 and 1.0")  
        if not 0.0 <= self.confidence.entity_threshold <= 1.0:
            errors.append("entity_threshold must be between 0.0 and 1.0")
            
        # Validate entity-specific thresholds
        for entity_type, threshold in self.confidence.entity_specific.items():
            if not 0.0 <= threshold <= 1.0:
                errors.append(f"entity_specific threshold for '{entity_type}' must be between 0.0 and 1.0")
        
        # Validate performance settings
        if self.performance.max_text_length <= 0:
            errors.append("max_text_length must be positive")
        if self.performance.processing_timeout <= 0:
            errors.append("processing_timeout must be positive")
            
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level not in valid_log_levels:
            errors.append(f"log level must be one of: {valid_log_levels}")
            
        return errors


def load_config(config_path: Optional[Union[str, Path]] = None) -> SDKConfig:
    """Load SDK configuration from file or defaults.
    
    Args:
        config_path: Optional path to configuration file. If None, loads defaults.
        
    Returns:
        SDKConfig instance.
    """
    if config_path is None:
        return SDKConfig.load_default()
    else:
        return SDKConfig.load_from_file(config_path)