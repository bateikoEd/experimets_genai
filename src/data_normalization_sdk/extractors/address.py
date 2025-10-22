"""Address extraction from unstructured text."""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..core.base import BaseExtractor, EntityResult, EntityType, ProcessingMetadata


class AddressExtractor(BaseExtractor):
    """Extract address information from text."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize address extractor with configuration."""
        super().__init__(config)
        self.name = "address_extractor"
        
        # Address component patterns
        self.patterns = {
            'bill_to': re.compile(r'Bill\s+To:\s*(.+)', re.IGNORECASE),
            'ship_to': re.compile(r'Ship\s+To:\s*(.+)', re.IGNORECASE),
            'name': re.compile(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)', re.MULTILINE),
            'street': re.compile(r'(\d+[\/\-\w]*\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)?)', re.IGNORECASE),
            'postal_code': re.compile(r'\b(\d{5,6})\b'),
            'city': re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*(?:\s+City)?)', re.IGNORECASE),
            'district': re.compile(r'(?:District|Dist\.?|Ward)\s*(\d+)', re.IGNORECASE),
            'country': re.compile(r'\b(Vietnam|USA|United States|UK|United Kingdom|Germany|France|Japan|China|India|Brazil|Canada|Australia)\b', re.IGNORECASE),
        }
        
        # Country code mapping
        self.country_codes = {
            'vietnam': 'VNM',
            'usa': 'USA',
            'united states': 'USA',
            'uk': 'GBR', 
            'united kingdom': 'GBR',
            'germany': 'DEU',
            'france': 'FRA',
            'japan': 'JPN',
            'china': 'CHN',
            'india': 'IND',
            'brazil': 'BRA',
            'canada': 'CAN',
            'australia': 'AUS'
        }
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract address information from text."""
        # Look for "Bill To:" or "Ship To:" patterns first
        bill_to_match = self.patterns['bill_to'].search(text)
        ship_to_match = self.patterns['ship_to'].search(text)
        
        if bill_to_match or ship_to_match:
            # Process the address portion after "Bill To:" or "Ship To:"
            address_text = bill_to_match.group(1) if bill_to_match else ship_to_match.group(1)
            result = self._parse_address_components(address_text, text)
            if result:
                return result.attributes, result.metadata.confidence
        else:
            # Try to extract address from entire text
            result = self._parse_address_components(text, text)
            if result:
                return result.attributes, result.metadata.confidence
        
        return {}, 0.0
    
    def _parse_address_components(self, address_text: str, full_text: str) -> Optional[EntityResult]:
        """Parse individual address components."""
        attributes = {}
        confidence_factors = []
        
        # Split address text by commas for component parsing
        parts = [part.strip() for part in address_text.split(',')]
        
        # Extract person name (first part if it looks like a name)
        if parts and self._looks_like_name(parts[0]):
            person_name = self._parse_name(parts[0])
            if person_name:
                attributes['person'] = person_name
                confidence_factors.append(0.9)
                parts = parts[1:]  # Remove name from remaining parts
        
        # Extract street address
        street_match = self.patterns['street'].search(' '.join(parts[:2]) if len(parts) > 1 else parts[0] if parts else '')
        if street_match:
            attributes['street_address'] = street_match.group(1).strip()
            confidence_factors.append(0.95)
        
        # Extract district
        district_match = self.patterns['district'].search(address_text)
        if district_match:
            attributes['district'] = f"District {district_match.group(1)}"
            confidence_factors.append(0.9)
        
        # Extract city (look for capitalized words that aren't countries)
        for part in reversed(parts):
            if self._looks_like_city(part) and not self._is_country(part):
                # Remove postal code if present
                city_clean = re.sub(r'\s*\d{5,6}\s*', '', part).strip()
                if city_clean:
                    attributes['city'] = city_clean
                    confidence_factors.append(0.85)
                break
        
        # Extract postal code
        postal_match = self.patterns['postal_code'].search(address_text)
        if postal_match:
            attributes['postal_code'] = postal_match.group(1)
            confidence_factors.append(0.95)
        
        # Extract country
        country_match = self.patterns['country'].search(address_text)
        if country_match:
            country_name = country_match.group(1)
            attributes['country_name'] = country_name
            country_code = self.country_codes.get(country_name.lower())
            if country_code:
                attributes['country_code'] = country_code
                confidence_factors.append(0.98)
        
        # Set region to null as not specified
        attributes['region'] = None
        
        # Calculate confidence
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        
        # Only return if we found meaningful address components
        if len(attributes) >= 3:  # At least 3 components to be considered valid
            metadata = ProcessingMetadata(
                source="text_extraction",
                transformations=["address_parsing", "component_extraction"],
                confidence=min(confidence, 1.0),
                parser_version="1.2.0",
                normalization_ruleset="UPU/CLDR"
            )
            
            return EntityResult(
                entity_type=EntityType.ADDRESS,
                attributes=attributes,
                metadata=metadata
            )
        
        return None
    
    def _looks_like_name(self, text: str) -> bool:
        """Check if text looks like a person's name."""
        # Simple heuristic: starts with capital letter, has 2-4 parts, no numbers
        parts = text.split()
        if len(parts) < 2 or len(parts) > 4:
            return False
        
        # All parts should start with capital letter and contain no digits
        for part in parts:
            if not part[0].isupper() or any(c.isdigit() for c in part):
                return False
        
        return True
    
    def _parse_name(self, name_text: str) -> Dict[str, str]:
        """Parse name into components."""
        parts = name_text.split()
        if len(parts) == 2:
            return {
                "given_name": parts[0],
                "middle_name": None,
                "family_name": parts[1]
            }
        elif len(parts) == 3:
            return {
                "given_name": parts[0],
                "middle_name": parts[1],
                "family_name": parts[2]
            }
        elif len(parts) >= 4:
            return {
                "given_name": parts[0],
                "middle_name": ' '.join(parts[1:-1]),
                "family_name": parts[-1]
            }
        else:
            return {
                "given_name": parts[0],
                "middle_name": None,
                "family_name": None
            }
    
    def _looks_like_city(self, text: str) -> bool:
        """Check if text looks like a city name."""
        # Remove postal codes and check if remaining text looks like a city
        clean_text = re.sub(r'\s*\d{5,6}\s*', '', text).strip()
        return bool(clean_text and clean_text[0].isupper() and not any(c.isdigit() for c in clean_text))
    
    def _is_country(self, text: str) -> bool:
        """Check if text is a country name."""
        return text.lower().strip() in self.country_codes
    
    def get_name(self) -> str:
        """Get the extractor name."""
        return self.name
    
    @property
    def supported_entity_types(self) -> set:
        """Get list of entity types this extractor can handle."""
        return {EntityType.ADDRESS}