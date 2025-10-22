"""People extraction from unstructured text."""

import re
import unicodedata
from typing import Dict, Any, Tuple
from ..core.base import BaseExtractor, EntityType


class PeopleExtractor(BaseExtractor):
    """Extract people information from text."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize people extractor with configuration."""
        super().__init__(config)
        self.name = "people_extractor"
        
        # People patterns
        self.patterns = {
            # Prof. François L'Écuyer (CTO) — francois.lecuyer@example.fr — +33 (0)1 23 45 67 89
            'full_person': re.compile(
                r'^(Prof\.|Dr\.|Mr\.|Ms\.|Mrs\.)?\s*([^(]+?)\s*\(([^)]+)\)\s*[—\-]\s*'
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*[—\-]\s*'
                r'(\+\d+\s*\(\d+\)\d+\s*\d+\s*\d+\s*\d+\s*\d+)',
                re.IGNORECASE
            ),
            'honorific': re.compile(r'^(Prof\.|Dr\.|Mr\.|Ms\.|Mrs\.)\s*', re.IGNORECASE),
            'name': re.compile(r'^(?:Prof\.|Dr\.|Mr\.|Ms\.|Mrs\.)?\s*([A-Za-zÀ-ÿ\s\']+?)(?:\s*\([^)]+\))?', re.IGNORECASE),
            'role': re.compile(r'\(([^)]+)\)', re.IGNORECASE),
            'email': re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),
            'phone': re.compile(r'(\+\d+\s*\(\d+\)\d+\s*\d+\s*\d+\s*\d+\s*\d+)'),
        }
        
        # Country code mapping based on phone prefixes
        self.country_codes = {
            '+33': 'FRA',  # France
            '+1': 'USA',   # USA/Canada
            '+44': 'GBR',  # UK
            '+49': 'DEU',  # Germany
            '+81': 'JPN',  # Japan
        }
    
    @property
    def supported_entity_types(self) -> set:
        """Get entity types this extractor can handle."""
        return {EntityType.PERSON}
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract people information from text."""
        attributes = {}
        confidence_factors = []
        
        # Try full person pattern
        full_match = self.patterns['full_person'].search(text.strip())
        if full_match:
            honorific, name, role, email, phone = full_match.groups()
            
            # Extract honorific
            if honorific:
                attributes['honorific'] = honorific.strip()
                confidence_factors.append(0.98)  # Higher confidence for complete person pattern
            
            # Extract name
            full_name = name.strip()
            attributes['full_name'] = full_name
            
            # Create ASCII version
            ascii_name = self._to_ascii(full_name)
            if ascii_name != full_name:
                attributes['ascii_full_name'] = ascii_name
            
            confidence_factors.append(0.99)  # Very high confidence for name in full pattern
            
            # Extract role
            if role:
                attributes['role'] = role.strip()
                confidence_factors.append(0.98)  # High confidence for role
            
            # Extract email
            if email:
                attributes['email'] = email.strip()
                confidence_factors.append(0.97)  # High confidence for email in person context
            
            # Extract and normalize phone
            if phone:
                normalized_phone = self._normalize_phone(phone)
                if normalized_phone:
                    attributes['phone_e164'] = normalized_phone
                    
                    # Infer country code
                    country_code = self._infer_country_code(normalized_phone)
                    if country_code:
                        attributes['country_code_inferred'] = country_code
                    
                    confidence_factors.append(0.97)  # High confidence for phone in person context
        
        else:
            # Try individual patterns
            honorific_match = self.patterns['honorific'].search(text)
            if honorific_match:
                attributes['honorific'] = honorific_match.group(1)
                confidence_factors.append(0.75)
            
            name_match = self.patterns['name'].search(text)
            if name_match:
                full_name = name_match.group(1).strip()
                attributes['full_name'] = full_name
                
                # Create ASCII version
                ascii_name = self._to_ascii(full_name)
                if ascii_name != full_name:
                    attributes['ascii_full_name'] = ascii_name
                
                confidence_factors.append(0.80)
            
            role_match = self.patterns['role'].search(text)
            if role_match:
                attributes['role'] = role_match.group(1).strip()
                confidence_factors.append(0.75)
            
            email_match = self.patterns['email'].search(text)
            if email_match:
                attributes['email'] = email_match.group(1)
                confidence_factors.append(0.85)
            
            phone_match = self.patterns['phone'].search(text)
            if phone_match:
                normalized_phone = self._normalize_phone(phone_match.group(1))
                if normalized_phone:
                    attributes['phone_e164'] = normalized_phone
                    
                    country_code = self._infer_country_code(normalized_phone)
                    if country_code:
                        attributes['country_code_inferred'] = country_code
                    
                    confidence_factors.append(0.80)
        
        # Calculate confidence
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
        
        # Only return if we found meaningful person information
        if len(attributes) >= 2:  # At least name and one other attribute
            return attributes, min(confidence, 1.0)
        
        return {}, 0.0
    
    def _to_ascii(self, text: str) -> str:
        """Convert Unicode text to ASCII equivalent."""
        # Normalize to NFD (decomposed) form and remove diacritics
        nfd = unicodedata.normalize('NFD', text)
        ascii_text = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
        return ascii_text
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format."""
        # Remove spaces, parentheses, and other formatting
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Handle French format with trunk prefix (0)
        if cleaned.startswith('+33'):
            # Remove trunk prefix 0 if present after country code
            if len(cleaned) > 3 and cleaned[3] == '0':
                cleaned = cleaned[:3] + cleaned[4:]
        
        return cleaned
    
    def _infer_country_code(self, phone_e164: str) -> str:
        """Infer country code from E.164 phone number."""
        for prefix, country in self.country_codes.items():
            if phone_e164.startswith(prefix):
                return country
        return None
    
    def get_name(self) -> str:
        """Get the extractor name."""
        return self.name