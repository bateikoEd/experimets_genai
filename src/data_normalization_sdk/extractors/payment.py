"""Payment extraction from unstructured text."""

import re
from typing import Dict, Any, Tuple
from datetime import datetime
from ..core.base import BaseExtractor, EntityType


class PaymentExtractor(BaseExtractor):
    """Extract payment information from text."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize payment extractor with configuration."""
        super().__init__(config)
        self.name = "payment_extractor"
        
        # Payment patterns
        self.patterns = {
            # Paid: 5,000 JPY via card on 2025-08-01 14:22 JST (Auth: 9ZK12)
            'full_payment': re.compile(
                r'Paid:\s*([\d,]+(?:\.\d+)?)\s*([A-Z]{3})\s+via\s+(\w+)\s+on\s+'
                r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s*([A-Z]{3,4})?\s*'
                r'\(Auth:\s*([A-Z0-9]+)\)',
                re.IGNORECASE
            ),
            'amount': re.compile(r'([\d,]+(?:\.\d+)?)\s*([A-Z]{3})', re.IGNORECASE),
            'method': re.compile(r'via\s+(\w+)', re.IGNORECASE),
            'date': re.compile(r'(\d{4}-\d{2}-\d{2})', re.IGNORECASE),
            'time': re.compile(r'(\d{2}:\d{2})', re.IGNORECASE),
            'timezone': re.compile(r'\b([A-Z]{3,4})\b', re.IGNORECASE),
            'auth_code': re.compile(r'Auth[:\s]+([A-Z0-9]+)', re.IGNORECASE),
        }
        
        # Currency minor unit mapping (ISO 4217)
        self.currency_minor_units = {
            'JPY': 0,  # No decimal places
            'USD': 2,  # 2 decimal places
            'EUR': 2,
            'GBP': 2,
            'KRW': 0,
            'VND': 0,
        }
        
        # Timezone offset mapping
        self.timezone_offsets = {
            'JST': '+09:00',  # Japan Standard Time
            'EST': '-05:00',  # Eastern Standard Time
            'PST': '-08:00',  # Pacific Standard Time
            'UTC': '+00:00',
            'GMT': '+00:00',
        }
    
    @property
    def supported_entity_types(self) -> set:
        """Get entity types this extractor can handle."""
        return {EntityType.PAYMENT}
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract payment information from text."""
        attributes = {}
        confidence_factors = []
        
        # Try full payment pattern
        full_match = self.patterns['full_payment'].search(text)
        if full_match:
            amount_str, currency, method, date_part, time_part, timezone, auth_code = full_match.groups()
            
            # Extract amount and currency
            amount = float(amount_str.replace(',', ''))
            attributes['amount'] = amount
            attributes['currency_code'] = currency.upper()
            confidence_factors.append(0.95)
            
            # Calculate minor units
            minor_unit_exp = self.currency_minor_units.get(currency.upper(), 2)
            attributes['amount_in_minor_units'] = int(amount * (10 ** minor_unit_exp))
            confidence_factors.append(0.90)
            
            # Extract method
            attributes['method'] = method.upper()
            confidence_factors.append(0.90)
            
            # Extract datetime
            paid_at = self._parse_datetime(date_part, time_part, timezone)
            if paid_at:
                attributes['paid_at'] = paid_at
                confidence_factors.append(0.90)
            
            # Extract authorization code
            if auth_code:
                attributes['authorized_code'] = auth_code
                confidence_factors.append(0.85)
        
        else:
            # Try individual patterns
            amount_match = self.patterns['amount'].search(text)
            if amount_match:
                amount_str, currency = amount_match.groups()
                amount = float(amount_str.replace(',', ''))
                attributes['amount'] = amount
                attributes['currency_code'] = currency.upper()
                
                # Calculate minor units
                minor_unit_exp = self.currency_minor_units.get(currency.upper(), 2)
                attributes['amount_in_minor_units'] = int(amount * (10 ** minor_unit_exp))
                confidence_factors.append(0.80)
            
            method_match = self.patterns['method'].search(text)
            if method_match:
                attributes['method'] = method_match.group(1).upper()
                confidence_factors.append(0.75)
            
            # Extract datetime components
            date_match = self.patterns['date'].search(text)
            time_match = self.patterns['time'].search(text)
            timezone_match = self.patterns['timezone'].search(text)
            
            if date_match and time_match:
                date_part = date_match.group(1)
                time_part = time_match.group(1)
                timezone = timezone_match.group(1) if timezone_match else None
                
                paid_at = self._parse_datetime(date_part, time_part, timezone)
                if paid_at:
                    attributes['paid_at'] = paid_at
                    confidence_factors.append(0.75)
            
            auth_match = self.patterns['auth_code'].search(text)
            if auth_match:
                attributes['authorized_code'] = auth_match.group(1)
                confidence_factors.append(0.70)
        
        # Calculate confidence
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
        
        # Only return if we found meaningful payment information
        if len(attributes) >= 2:  # At least amount+currency or similar
            return attributes, min(confidence, 1.0)
        
        return {}, 0.0
    
    def _parse_datetime(self, date_part: str, time_part: str, timezone: str = None) -> str:
        """Parse datetime to ISO 8601 format."""
        try:
            # Parse datetime
            dt_str = f"{date_part} {time_part}"
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            
            # Add timezone offset
            if timezone and timezone.upper() in self.timezone_offsets:
                tz_offset = self.timezone_offsets[timezone.upper()]
                return dt.isoformat() + tz_offset
            else:
                return dt.isoformat()
                
        except ValueError:
            return None
    
    def get_name(self) -> str:
        """Get the extractor name."""
        return self.name