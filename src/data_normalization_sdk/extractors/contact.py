"""Contact information extraction from unstructured text."""

import re
import phonenumbers
from typing import List, Dict, Any, Optional, Tuple
from ..core.base import BaseExtractor, EntityResult, EntityType, ProcessingMetadata


class ContactExtractor(BaseExtractor):
    """Extract contact information (phone, email) from text."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize contact extractor with configuration."""
        super().__init__(config)
        self.name = "contact_extractor"
        
        # Phone number patterns
        self.phone_patterns = [
            re.compile(r'\((\d{3})\)\s*(\d{3})-(\d{2})-(\d{2})(?:\s*ext\.?\s*(\d+))?', re.IGNORECASE),  # (044) 123-45-67 ext 123
            re.compile(r'\+(\d{1,3})[\s\-\.]?(\d{2,3})[\s\-\.]?(\d{3})[\s\-\.]?(\d{2})[\s\-\.]?(\d{2})(?:\s*ext\.?\s*(\d+))?', re.IGNORECASE),  # +33 1 23 45 67 89
            re.compile(r'\+(\d{1,4})[\s\-\.\(]?(\d{1,4})[\s\-\.\)]?[\s\-\.]?(\d{3,4})[\s\-\.]?(\d{2,4})[\s\-\.]?(\d{0,4})(?:\s*ext\.?\s*(\d+))?', re.IGNORECASE),  # General international
            re.compile(r'(\d{3})[\s\-\.](\d{3})[\s\-\.](\d{4})(?:\s*ext\.?\s*(\d+))?'),  # 123-456-7890 ext 123
        ]
        
        # Email patterns
        self.email_patterns = [
            re.compile(r'([a-zA-Z0-9._%+-]+)\[at\]([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE),  # email[at]domain.com
            re.compile(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'),  # standard email
        ]
        
        # Area code to country mapping (partial)
        self.area_code_countries = {
            '044': 'UKR',  # Ukraine Kyiv
            '380': 'UKR',  # Ukraine
            '1': 'USA',    # USA/Canada
            '33': 'FRA',   # France
            '49': 'DEU',   # Germany
            '44': 'GBR',   # UK
            '81': 'JPN',   # Japan
            '86': 'CHN',   # China
        }
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract contact information from text."""
        # Extract phone and email from the same text
        phone_info = self._extract_phone(text)
        email_info = self._extract_email(text)
        
        # Combine if both found, or create separate results
        if phone_info or email_info:
            attributes = {}
            confidence_factors = []
            
            if phone_info:
                attributes.update(phone_info['attributes'])
                confidence_factors.append(phone_info['confidence'])
            
            if email_info:
                attributes.update(email_info['attributes'])
                confidence_factors.append(email_info['confidence'])
            
            # Calculate overall confidence
            confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
            
            # Reduce confidence if this looks like a person profile
            if self._looks_like_person_profile(text):
                confidence *= 0.80  # Reduce confidence by 20% to favor person extractor
            
            return attributes, min(confidence, 1.0)
        
        return {}, 0.0
    
    def _extract_phone(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract phone number information."""
        for pattern in self.phone_patterns:
            match = pattern.search(text)
            if match:
                return self._process_phone_match(match, text)
        return None
    
    def _process_phone_match(self, match: re.Match, original_text: str) -> Dict[str, Any]:
        """Process a phone number regex match."""
        groups = match.groups()
        transformations = ["strip_punctuation"]
        
        # Handle different phone formats
        if '(044)' in original_text:
            # Ukrainian format: (044) 123-45-67
            area_code = groups[0]
            number_parts = groups[1:4]
            extension = groups[4] if len(groups) > 4 and groups[4] else None
            
            # Convert to E.164
            phone_e164 = f"+380{area_code}{number_parts[0]}{number_parts[1]}{number_parts[2]}"
            country_code = 'UKR'
            transformations.append("country_infer_by_area_code")
            
        elif match.pattern.pattern.startswith(r'\+'):
            # International format: +33 1 23 45 67 89
            country_code_num = groups[0]
            number_parts = [g for g in groups[1:] if g and g.isdigit()]
            extension = None
            
            # Look for extension in later groups
            for g in groups:
                if g and g.isdigit() and len(g) <= 4 and groups.index(g) == len(groups) - 1:
                    extension = g
                    number_parts = number_parts[:-1]
                    break
            
            phone_e164 = f"+{country_code_num}{''.join(number_parts)}"
            country_code = self.area_code_countries.get(country_code_num, 'UNKNOWN')
            
            # Handle specific formatting (e.g., French format with trunk prefix removal)
            if country_code_num == '33' and number_parts and number_parts[0].startswith('0'):
                # Remove trunk prefix 0
                number_parts[0] = number_parts[0][1:]
                phone_e164 = f"+{country_code_num}{''.join(number_parts)}"
                transformations.append("remove_trunk_prefix_0")
        
        else:
            # Domestic format - assume US/Canada for now
            phone_e164 = f"+1{''.join(groups[:3])}"
            country_code = 'USA'
        
        attributes = {
            "phone_e164": phone_e164,
            "country_code_inferred": country_code
        }
        
        if extension:
            attributes["phone_extension"] = extension
        
        return {
            "attributes": attributes,
            "transformations": transformations,
            "confidence": 0.99
        }
    
    def _extract_email(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract email information."""
        for pattern in self.email_patterns:
            match = pattern.search(text)
            if match:
                return self._process_email_match(match, pattern)
        return None
    
    def _process_email_match(self, match: re.Match, pattern: re.Pattern) -> Dict[str, Any]:
        """Process an email regex match."""
        transformations = []
        
        if '[at]' in match.group(0):
            # Handle obfuscated email: user[at]domain.com
            email = f"{match.group(1)}@{match.group(2)}"
            transformations.append("replace_[at]_with_@")
        else:
            # Standard email format
            email = match.group(0)
        
        attributes = {
            "email": email
        }
        
        return {
            "attributes": attributes,
            "transformations": transformations,
            "confidence": 0.99
        }
    
    def _looks_like_person_profile(self, text: str) -> bool:
        """Check if text looks like a person profile rather than just contact info."""
        # Look for patterns that indicate a person profile
        person_indicators = [
            re.compile(r'(Prof\.|Dr\.|Mr\.|Ms\.|Mrs\.)', re.IGNORECASE),  # Honorifics
            re.compile(r'\([A-Z]{2,4}\)', re.IGNORECASE),  # Role in parentheses like (CTO)
            re.compile(r'[A-Za-z]+\s+[A-Za-z\']+.*—.*@.*—.*\+', re.IGNORECASE),  # Full name — email — phone pattern
        ]
        
        for pattern in person_indicators:
            if pattern.search(text):
                return True
        return False

    def get_name(self) -> str:
        """Get the extractor name."""
        return self.name
    
    @property
    def supported_entity_types(self) -> set:
        """Get list of entity types this extractor can handle."""
        return {EntityType.CONTACT}