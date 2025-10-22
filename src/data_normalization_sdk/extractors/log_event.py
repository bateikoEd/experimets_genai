"""Log event extraction from unstructured text."""

import re
from typing import Dict, Any, Tuple
from datetime import datetime
from ..core.base import BaseExtractor, EntityType


class LogEventExtractor(BaseExtractor):
    """Extract log event information from text."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize log event extractor with configuration."""
        super().__init__(config)
        self.name = "log_event_extractor"
        
        # Log event patterns
        self.patterns = {
            # WARN [Payments] 2025/09/17 08:45:10 UTC user=984 ip=10.0.1.5 msg='Retryable timeout'
            'full_log': re.compile(
                r'(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)\s*'
                r'\[([^\]]+)\]\s*'
                r'(\d{4}[\/\-]\d{2}[\/\-]\d{2})\s+'
                r'(\d{2}:\d{2}:\d{2})\s*'
                r'(UTC|GMT|[A-Z]{3,4})?\s*'
                r'(.+)',
                re.IGNORECASE
            ),
            'level': re.compile(r'^(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)', re.IGNORECASE),
            'component': re.compile(r'\[([^\]]+)\]', re.IGNORECASE),
            'timestamp': re.compile(r'(\d{4}[\/\-]\d{2}[\/\-]\d{2})\s+(\d{2}:\d{2}:\d{2})', re.IGNORECASE),
            'timezone': re.compile(r'\b(UTC|GMT|[A-Z]{3,4})\b', re.IGNORECASE),
            'user_id': re.compile(r'user[=:]\s*(\w+)', re.IGNORECASE),
            'ip_address': re.compile(r'ip[=:]\s*(\d+\.\d+\.\d+\.\d+)', re.IGNORECASE),
            'message': re.compile(r"msg[=:]\s*['\"]?([^'\"]+)['\"]?", re.IGNORECASE),
        }
    
    @property
    def supported_entity_types(self) -> set:
        """Get entity types this extractor can handle."""
        return {EntityType.LOG_EVENT}
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract log event information from text."""
        attributes = {}
        confidence_factors = []
        
        # Try full log pattern first
        full_match = self.patterns['full_log'].search(text)
        if full_match:
            level, component, date_part, time_part, timezone, rest = full_match.groups()
            
            # Extract level
            attributes['level'] = level.upper()
            confidence_factors.append(0.95)
            
            # Extract component
            attributes['component'] = component
            confidence_factors.append(0.90)
            
            # Extract timestamp
            timestamp_info = self._parse_timestamp(date_part, time_part, timezone)
            if timestamp_info:
                attributes['timestamp'] = timestamp_info
                confidence_factors.append(0.95)
            
            # Extract additional fields from the rest
            additional_info = self._parse_additional_fields(rest)
            if additional_info:
                attributes.update(additional_info)
                confidence_factors.extend([0.85] * len(additional_info))
        
        else:
            # Try individual patterns
            level_match = self.patterns['level'].search(text)
            if level_match:
                attributes['level'] = level_match.group(1).upper()
                confidence_factors.append(0.80)
            
            component_match = self.patterns['component'].search(text)
            if component_match:
                attributes['component'] = component_match.group(1)
                confidence_factors.append(0.75)
            
            timestamp_match = self.patterns['timestamp'].search(text)
            if timestamp_match:
                date_part, time_part = timestamp_match.groups()
                timezone_match = self.patterns['timezone'].search(text)
                timezone = timezone_match.group(1) if timezone_match else None
                
                timestamp_info = self._parse_timestamp(date_part, time_part, timezone)
                if timestamp_info:
                    attributes['timestamp'] = timestamp_info
                    confidence_factors.append(0.80)
            
            # Extract additional fields
            additional_info = self._parse_additional_fields(text)
            if additional_info:
                attributes.update(additional_info)
                confidence_factors.extend([0.70] * len(additional_info))
        
        # Calculate confidence
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
        
        # Only return if we found meaningful log event information
        if len(attributes) >= 2:  # At least level and one other attribute
            return attributes, min(confidence, 1.0)
        
        return {}, 0.0
    
    def _parse_timestamp(self, date_part: str, time_part: str, timezone: str = None) -> str:
        """Parse timestamp to ISO 8601 format."""
        try:
            # Normalize date separators
            date_normalized = date_part.replace('/', '-')
            
            # Parse datetime
            dt_str = f"{date_normalized} {time_part}"
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            
            # Format to ISO 8601
            if timezone and timezone.upper() in ['UTC', 'GMT']:
                return dt.isoformat() + 'Z'
            else:
                return dt.isoformat()
                
        except ValueError:
            return None
    
    def _parse_additional_fields(self, text: str) -> Dict[str, str]:
        """Parse additional fields like user_id, ip, message."""
        fields = {}
        
        # Extract user ID
        user_match = self.patterns['user_id'].search(text)
        if user_match:
            fields['user_id'] = user_match.group(1)
        
        # Extract IP address
        ip_match = self.patterns['ip_address'].search(text)
        if ip_match:
            fields['ip'] = ip_match.group(1)
        
        # Extract message
        msg_match = self.patterns['message'].search(text)
        if msg_match:
            fields['message'] = msg_match.group(1).strip()
        
        return fields
    
    def get_name(self) -> str:
        """Get the extractor name."""
        return self.name