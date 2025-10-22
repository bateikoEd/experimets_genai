"""Product information extraction from unstructured text."""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..core.base import BaseExtractor, EntityResult, EntityType, ProcessingMetadata


class ProductExtractor(BaseExtractor):
    """Extract product information from text."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize product extractor with configuration."""
        super().__init__(config)
        self.name = "product_extractor"
        
        # Product parsing patterns
        self.patterns = {
            'name': re.compile(r'Name:\s*([^—]+?)(?:\s+\d+(?:kg|g|lb|oz|ml|l))?(?:\s*—|\s*$)', re.IGNORECASE),
            'weight': re.compile(r'(\d+(?:\.\d+)?)\s*(kg|g|lb|oz)', re.IGNORECASE),
            'volume': re.compile(r'(\d+(?:\.\d+)?)\s*(ml|l|fl\s*oz)', re.IGNORECASE),
            'price_eur': re.compile(r'€\s*(\d+(?:[,.]\d+)?)', re.IGNORECASE),
            'price_usd': re.compile(r'\$\s*(\d+(?:[,.]\d+)?)', re.IGNORECASE),
            'price_gbp': re.compile(r'£\s*(\d+(?:[,.]\d+)?)', re.IGNORECASE),
            'price_general': re.compile(r'Price:\s*([€$£¥])\s*(\d+(?:[,.]\d+)?)', re.IGNORECASE),
            'category': re.compile(r'Category:\s*([^—\n]+)', re.IGNORECASE),
        }
        
        # Currency symbol mapping
        self.currency_symbols = {
            '€': 'EUR',
            '$': 'USD',
            '£': 'GBP',
            '¥': 'JPY',
        }
        
        # Weight unit conversions to kg
        self.weight_to_kg = {
            'kg': 1.0,
            'g': 0.001,
            'lb': 0.453592,
            'oz': 0.0283495,
        }
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract product information from text."""
        attributes = {}
        confidence_factors = []
        
        # Extract product name
        name_match = self.patterns['name'].search(text)
        if name_match:
            name = name_match.group(1).strip()
            attributes['name'] = name
            confidence_factors.append(0.95)
        
        # Extract weight/volume
        weight_match = self.patterns['weight'].search(text)
        if weight_match:
            weight_value = float(weight_match.group(1).replace(',', '.'))
            weight_unit = weight_match.group(2).lower()
            
            # Convert to kg
            weight_kg = weight_value * self.weight_to_kg.get(weight_unit, 1.0)
            attributes['net_weight_kg'] = weight_kg
            confidence_factors.append(0.90)
        
        # Extract price
        price_info = self._extract_price(text)
        if price_info:
            attributes.update(price_info['attributes'])
            confidence_factors.append(price_info['confidence'])
        
        # Extract category
        category_match = self.patterns['category'].search(text)
        if category_match:
            category_text = category_match.group(1).strip()
            # Split category path by > or similar delimiters
            if '>' in category_text:
                category_path = [cat.strip() for cat in category_text.split('>')]
            elif '/' in category_text:
                category_path = [cat.strip() for cat in category_text.split('/')]
            else:
                category_path = [category_text]
            
            attributes['category_path'] = category_path
            confidence_factors.append(0.85)
        
        # Calculate confidence
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        
        # Only return if we found meaningful product information
        if len(attributes) >= 2:  # At least name and one other attribute
            return attributes, min(confidence, 1.0)
        
        return {}, 0.0
    
    def _extract_price(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract price and currency information."""
        # Try specific currency patterns first
        for currency_pattern, currency_code in [
            (self.patterns['price_eur'], 'EUR'),
            (self.patterns['price_usd'], 'USD'),
            (self.patterns['price_gbp'], 'GBP'),
        ]:
            match = currency_pattern.search(text)
            if match:
                price_str = match.group(1).replace(',', '.')
                price = float(price_str)
                
                # Infer locale based on currency and decimal separator
                locale = None
                if currency_code == 'EUR':
                    if ',' in match.group(1):
                        locale = 'de-DE'  # German/European format
                    else:
                        locale = 'en-EU'
                
                return {
                    'attributes': {
                        'price': price,
                        'currency_code': currency_code
                    },
                    'confidence': 0.96,
                    'locale': locale
                }
        
        # Try general price pattern
        general_match = self.patterns['price_general'].search(text)
        if general_match:
            currency_symbol = general_match.group(1)
            price_str = general_match.group(2).replace(',', '.')
            price = float(price_str)
            currency_code = self.currency_symbols.get(currency_symbol, 'UNKNOWN')
            
            return {
                'attributes': {
                    'price': price,
                    'currency_code': currency_code
                },
                'confidence': 0.90
            }
        
        return None
    
    def get_name(self) -> str:
        """Get the extractor name."""
        return self.name
    
    @property
    def supported_entity_types(self) -> set:
        """Get list of entity types this extractor can handle."""
        return {EntityType.PRODUCT}