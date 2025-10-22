"""Measurement extraction from unstructured text."""

import re
from typing import Dict, Any, Tuple
from ..core.base import BaseExtractor, EntityType


class MeasurementExtractor(BaseExtractor):
    """Extract measurement/specification information from text."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize measurement extractor with configuration."""
        super().__init__(config)
        self.name = "measurement_extractor"
        
        # Measurement patterns
        self.patterns = {
            # Spec: 10 in × 6 in × 2.5 in; weight 1 lb 4 oz
            'dimensions': re.compile(
                r'(\d+(?:\.\d+)?)\s*(in|cm|mm|ft|m)[\s×x]\s*'
                r'(\d+(?:\.\d+)?)\s*(in|cm|mm|ft|m)[\s×x]\s*'
                r'(\d+(?:\.\d+)?)\s*(in|cm|mm|ft|m)',
                re.IGNORECASE
            ),
            'weight_lb_oz': re.compile(
                r'(\d+)\s*lb\s+(\d+)\s*oz',
                re.IGNORECASE
            ),
            'weight_simple': re.compile(
                r'(\d+(?:\.\d+)?)\s*(kg|lb|g|oz)',
                re.IGNORECASE
            ),
            'single_dimension': re.compile(
                r'(\d+(?:\.\d+)?)\s*(in|cm|mm|ft|m)',
                re.IGNORECASE
            ),
        }
        
        # Unit conversion factors
        self.conversions = {
            'in_to_cm': 2.54,
            'ft_to_cm': 30.48,
            'mm_to_cm': 0.1,
            'm_to_cm': 100.0,
            'lb_to_kg': 0.453592,
            'oz_to_kg': 0.0283495,
            'g_to_kg': 0.001,
        }
    
    @property
    def supported_entity_types(self) -> set:
        """Get entity types this extractor can handle."""
        return {EntityType.SPEC}
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract measurement information from text."""
        attributes = {}
        confidence_factors = []
        
        # Extract dimensions
        dim_match = self.patterns['dimensions'].search(text)
        if dim_match:
            length, unit1, width, unit2, height, unit3 = dim_match.groups()
            
            # Assume all dimensions use the same unit (from first one)
            unit = unit1.lower()
            
            length_val = float(length)
            width_val = float(width) 
            height_val = float(height)
            
            if unit == 'in':
                # Store both inches and converted cm
                attributes['dimensions_in'] = {
                    'length': length_val,
                    'width': width_val,
                    'height': height_val
                }
                
                attributes['dimensions_cm'] = {
                    'length': round(length_val * self.conversions['in_to_cm'], 2),
                    'width': round(width_val * self.conversions['in_to_cm'], 2),
                    'height': round(height_val * self.conversions['in_to_cm'], 2)
                }
                confidence_factors.append(0.95)
                
            elif unit == 'cm':
                # Store both cm and converted inches
                attributes['dimensions_cm'] = {
                    'length': length_val,
                    'width': width_val,
                    'height': height_val
                }
                
                attributes['dimensions_in'] = {
                    'length': round(length_val / self.conversions['in_to_cm'], 2),
                    'width': round(width_val / self.conversions['in_to_cm'], 2),
                    'height': round(height_val / self.conversions['in_to_cm'], 2)
                }
                confidence_factors.append(0.95)
        
        # Extract weight (lb + oz format)
        weight_lb_oz_match = self.patterns['weight_lb_oz'].search(text)
        if weight_lb_oz_match:
            lb, oz = weight_lb_oz_match.groups()
            
            # Convert to decimal pounds
            total_lb = float(lb) + float(oz) / 16.0
            attributes['weight_lb'] = round(total_lb, 2)
            
            # Convert to kg
            weight_kg = total_lb * self.conversions['lb_to_kg']
            attributes['weight_kg'] = round(weight_kg, 5)
            
            confidence_factors.append(0.90)
        
        # Extract simple weight
        else:
            weight_match = self.patterns['weight_simple'].search(text)
            if weight_match:
                weight_val, weight_unit = weight_match.groups()
                weight_val = float(weight_val)
                
                if weight_unit.lower() == 'lb':
                    attributes['weight_lb'] = weight_val
                    attributes['weight_kg'] = round(weight_val * self.conversions['lb_to_kg'], 5)
                    confidence_factors.append(0.85)
                    
                elif weight_unit.lower() == 'kg':
                    attributes['weight_kg'] = weight_val
                    attributes['weight_lb'] = round(weight_val / self.conversions['lb_to_kg'], 2)
                    confidence_factors.append(0.85)
        
        # Calculate confidence
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
        
        # Only return if we found meaningful measurement information
        if len(attributes) >= 1:  # At least dimensions or weight
            return attributes, min(confidence, 1.0)
        
        return {}, 0.0
    
    def get_name(self) -> str:
        """Get the extractor name."""
        return self.name