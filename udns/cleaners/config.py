"""
Cleaning configuration system for UDNS.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from .base import BaseCleaner


@dataclass
class CleaningConfig:
    """Configuration for cleaning pipeline."""
    
    # Global settings
    enabled: bool = True
    verbose: bool = False
    log_operations: bool = False
    
    # Pipeline settings
    pipeline_order: List[str] = field(default_factory=lambda: [
        "text_cleaner", "punctuation_cleaner", "case_cleaner", 
        "value_cleaner", "domain_cleaner"
    ])
    
    # Cleaner-specific configurations
    cleaner_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Entity type specific configurations
    entity_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Performance settings
    max_operations: int = 100
    timeout_seconds: float = 30.0
    
    # Quality settings
    min_confidence: float = 0.5
    skip_on_error: bool = False
    
    def __post_init__(self):
        """Validate configuration."""
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0.0 and 1.0")
        if self.max_operations <= 0:
            raise ValueError("max_operations must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
    
    def get_cleaner_config(self, cleaner_name: str) -> Dict[str, Any]:
        """Get configuration for a specific cleaner."""
        return self.cleaner_configs.get(cleaner_name, {})
    
    def get_entity_config(self, entity_type: str) -> Dict[str, Any]:
        """Get configuration for a specific entity type."""
        return self.entity_configs.get(entity_type, {})
    
    def set_cleaner_config(self, cleaner_name: str, config: Dict[str, Any]):
        """Set configuration for a specific cleaner."""
        self.cleaner_configs[cleaner_name] = config
    
    def set_entity_config(self, entity_type: str, config: Dict[str, Any]):
        """Set configuration for a specific entity type."""
        self.entity_configs[entity_type] = config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enabled': self.enabled,
            'verbose': self.verbose,
            'log_operations': self.log_operations,
            'pipeline_order': self.pipeline_order,
            'cleaner_configs': self.cleaner_configs,
            'entity_configs': self.entity_configs,
            'max_operations': self.max_operations,
            'timeout_seconds': self.timeout_seconds,
            'min_confidence': self.min_confidence,
            'skip_on_error': self.skip_on_error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CleaningConfig':
        """Create from dictionary."""
        return cls(**data)
    
    def save(self, file_path: Path, format: str = 'json'):
        """Save configuration to file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.to_dict()
        
        if format.lower() == 'json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format.lower() == 'yaml':
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @classmethod
    def load(cls, file_path: Path) -> 'CleaningConfig':
        """Load configuration from file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Determine format from file extension
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            format = 'yaml'
        else:
            format = 'json'
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if format == 'yaml':
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls.from_dict(data)


class ConfigManager:
    """Manager for cleaning configurations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager."""
        self.config_dir = config_dir or Path.cwd() / 'cleaning_configs'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configurations
        self.default_configs: Dict[str, CleaningConfig] = {}
        self._create_default_configs()
    
    def _create_default_configs(self):
        """Create default configurations for different entity types."""
        
        # Default text cleaning configuration
        text_config = {
            "remove_extra_spaces": True,
            "normalize_whitespace": True,
            "remove_control_chars": True,
            "normalize_unicode": True,
            "unicode_form": "NFC"
        }
        
        # Default punctuation cleaning configuration
        punctuation_config = {
            "preserve_essential": True,
            "standardize_quotes": True,
            "standardize_dashes": True,
            "standardize_ellipsis": True,
            "remove_redundant": True
        }
        
        # Default case cleaning configuration
        case_config = {
            "target_case": "sentence",
            "preserve_acronyms": True,
            "min_word_length": 3
        }
        
        # Default value cleaning configuration
        value_config = {
            "trim_whitespace": True,
            "remove_empty": True,
            "normalize_case": "preserve",
            "remove_special_chars": False
        }
        
        # Create default pipeline configuration
        default_config = CleaningConfig(
            enabled=True,
            pipeline_order=[
                "text_cleaner", "punctuation_cleaner", "case_cleaner", "value_cleaner"
            ],
            cleaner_configs={
                "text_cleaner": text_config,
                "punctuation_cleaner": punctuation_config,
                "case_cleaner": case_config,
                "value_cleaner": value_config
            }
        )
        
        # Entity-specific configurations
        invoice_config = CleaningConfig(
            enabled=True,
            pipeline_order=[
                "text_cleaner", "punctuation_cleaner", "value_cleaner", "invoice_cleaner"
            ],
            cleaner_configs={
                "text_cleaner": text_config,
                "punctuation_cleaner": punctuation_config,
                "value_cleaner": value_config,
                "invoice_cleaner": {
                    "normalize_invoice_numbers": True,
                    "standardize_currency": True,
                    "extract_dates": True
                }
            }
        )
        
        address_config = CleaningConfig(
            enabled=True,
            pipeline_order=[
                "text_cleaner", "punctuation_cleaner", "value_cleaner", "address_cleaner"
            ],
            cleaner_configs={
                "text_cleaner": text_config,
                "punctuation_cleaner": punctuation_config,
                "value_cleaner": value_config,
                "address_cleaner": {
                    "normalize_street": True,
                    "standardize_city": True,
                    "normalize_postal_code": True,
                    "validate_country": True
                }
            }
        )
        
        contact_config = CleaningConfig(
            enabled=True,
            pipeline_order=[
                "text_cleaner", "punctuation_cleaner", "value_cleaner", "contact_cleaner"
            ],
            cleaner_configs={
                "text_cleaner": text_config,
                "punctuation_cleaner": punctuation_config,
                "value_cleaner": value_config,
                "contact_cleaner": {
                    "normalize_phone": True,
                    "normalize_email": True,
                    "validate_contact": True
                }
            }
        )
        
        product_config = CleaningConfig(
            enabled=True,
            pipeline_order=[
                "text_cleaner", "punctuation_cleaner", "value_cleaner", "product_cleaner"
            ],
            cleaner_configs={
                "text_cleaner": text_config,
                "punctuation_cleaner": punctuation_config,
                "value_cleaner": value_config,
                "product_cleaner": {
                    "normalize_name": True,
                    "standardize_price": True,
                    "normalize_weight": True,
                    "extract_category": True
                }
            }
        )
        
        self.default_configs = {
            'default': default_config,
            'invoice': invoice_config,
            'address': address_config,
            'contact': contact_config,
            'product': product_config
        }
    
    def get_config(self, name: str = 'default') -> CleaningConfig:
        """Get a configuration by name."""
        if name in self.default_configs:
            return self.default_configs[name]
        
        # Try to load from file
        config_file = self.config_dir / f"{name}.json"
        if config_file.exists():
            return CleaningConfig.load(config_file)
        
        raise ValueError(f"Configuration '{name}' not found")
    
    def save_config(self, name: str, config: CleaningConfig, format: str = 'json'):
        """Save a configuration."""
        config_file = self.config_dir / f"{name}.{format}"
        config.save(config_file, format)
    
    def list_configs(self) -> List[str]:
        """List available configurations."""
        configs = list(self.default_configs.keys())
        
        # Add file-based configurations
        for file_path in self.config_dir.glob("*.json"):
            config_name = file_path.stem
            if config_name not in configs:
                configs.append(config_name)
        
        return sorted(configs)
    
    def create_config(self, name: str, base_config: Optional[str] = None) -> CleaningConfig:
        """Create a new configuration based on an existing one."""
        if base_config and base_config in self.default_configs:
            new_config = CleaningConfig.from_dict(
                self.default_configs[base_config].to_dict()
            )
        else:
            new_config = CleaningConfig()
        
        self.default_configs[name] = new_config
        return new_config
    
    def delete_config(self, name: str):
        """Delete a configuration."""
        if name in self.default_configs:
            del self.default_configs[name]
        
        # Delete file if it exists
        config_file = self.config_dir / f"{name}.json"
        if config_file.exists():
            config_file.unlink()
    
    def merge_configs(self, *config_names: str) -> CleaningConfig:
        """Merge multiple configurations."""
        if not config_names:
            return self.get_config('default')
        
        # Start with the first configuration
        merged_config = self.get_config(config_names[0])
        
        # Merge subsequent configurations
        for config_name in config_names[1:]:
            other_config = self.get_config(config_name)
            
            # Merge cleaner configs
            for cleaner_name, cleaner_config in other_config.cleaner_configs.items():
                if cleaner_name in merged_config.cleaner_configs:
                    # Deep merge
                    merged_config.cleaner_configs[cleaner_config].update(cleaner_config)
                else:
                    merged_config.cleaner_configs[cleaner_name] = cleaner_config
            
            # Merge entity configs
            for entity_name, entity_config in other_config.entity_configs.items():
                if entity_name in merged_config.entity_configs:
                    merged_config.entity_configs[entity_name].update(entity_config)
                else:
                    merged_config.entity_configs[entity_name] = entity_config
        
        return merged_config