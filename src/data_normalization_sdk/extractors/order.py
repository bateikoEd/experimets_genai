"""Order information extraction from unstructured text."""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from ..core.base import BaseExtractor, EntityResult, EntityType, ProcessingMetadata


class OrderExtractor(BaseExtractor):
    """Extract order information from text."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize order extractor with configuration."""
        super().__init__(config)
        self.name = "order_extractor"
        
        # Order parsing patterns
        self.patterns = {
            'items_section': re.compile(r'Items:\s*(.+?)(?:;|$)', re.IGNORECASE | re.DOTALL),
            'line_item': re.compile(r'(\d+)\s*[x×]\s*([A-Z0-9\-]+)\s*\(([^)]+)\)', re.IGNORECASE),
            'ship_date': re.compile(r'Ship\s+by:\s*(\d{4}-\d{2}-\d{2})', re.IGNORECASE),
            'delivery_date': re.compile(r'(?:Deliver|Delivery)\s+(?:by|date):\s*(\d{4}-\d{2}-\d{2})', re.IGNORECASE),
        }
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract order information from text."""
        attributes = {}
        confidence_factors = []
        
        # Extract line items
        items_info = self._extract_line_items(text)
        if items_info:
            attributes['lines'] = items_info['lines']
            confidence_factors.append(items_info['confidence'])
        
        # Extract shipping/delivery dates
        date_info = self._extract_dates(text)
        if date_info:
            attributes.update(date_info['attributes'])
            confidence_factors.append(date_info['confidence'])
        
        # Calculate confidence
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        
        # Only return if we found meaningful order information
        if attributes.get('lines') or date_info:
            return attributes, min(confidence, 1.0)
        
        return {}, 0.0
    
    def _extract_line_items(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract line items from order text."""
        items_match = self.patterns['items_section'].search(text)
        if not items_match:
            return None
        
        items_text = items_match.group(1)
        lines = []
        
        # Split by comma or semicolon and process each item
        item_strings = re.split(r'[,;]', items_text)
        
        for item_string in item_strings:
            item_string = item_string.strip()
            if not item_string:
                continue
            
            # Match pattern: "2 x SKU-1001 (Blue T-Shirt M)"
            line_match = self.patterns['line_item'].search(item_string)
            if line_match:
                quantity = int(line_match.group(1))
                sku = line_match.group(2)
                description = line_match.group(3)
                
                # Parse product name and variant from description
                name, variant = self._parse_product_description(description)
                
                line_item = {
                    "sku": sku,
                    "name": name,
                    "variant": variant,
                    "quantity": quantity
                }
                lines.append(line_item)
        
        if lines:
            return {
                "lines": lines,
                "confidence": 0.93
            }
        
        return None
    
    def _parse_product_description(self, description: str) -> tuple[str, Optional[str]]:
        """Parse product name and variant from description."""
        # Common patterns for variants at the end
        variant_patterns = [
            r'\s+([SMLXL]+)$',  # Size: S, M, L, XL, XXL, etc.
            r'\s+(\d+/\d+)$',   # Size: 32/32, 34/36, etc.
            r'\s+(\d+(?:\.\d+)?(?:kg|g|lb|oz|ml|l))$',  # Weight/volume
            r'\s+([A-Z]+\s*\d+)$',  # Model numbers like "V2", "PRO 3"
        ]
        
        for pattern in variant_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                variant = match.group(1)
                name = description[:match.start()].strip()
                return name, variant
        
        # No variant found, entire description is the name
        return description.strip(), None
    
    def _extract_dates(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract shipping and delivery dates."""
        attributes = {}
        confidence = 0.0
        
        # Extract ship date
        ship_match = self.patterns['ship_date'].search(text)
        if ship_match:
            ship_date = ship_match.group(1)
            # Validate date format
            try:
                datetime.strptime(ship_date, '%Y-%m-%d')
                attributes['requested_ship_date'] = ship_date
                confidence += 0.95
            except ValueError:
                pass
        
        # Extract delivery date
        delivery_match = self.patterns['delivery_date'].search(text)
        if delivery_match:
            delivery_date = delivery_match.group(1)
            try:
                datetime.strptime(delivery_date, '%Y-%m-%d')
                attributes['requested_delivery_date'] = delivery_date
                confidence += 0.95
            except ValueError:
                pass
        
        if attributes:
            return {
                "attributes": attributes,
                "confidence": min(confidence, 1.0)
            }
        
        return None
    
    def get_name(self) -> str:
        """Get the extractor name."""
        return self.name
    
    @property
    def supported_entity_types(self) -> set:
        """Get list of entity types this extractor can handle."""
        return {EntityType.ORDER}