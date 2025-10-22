"""
Domain-specific parsers for UDNS entity types.
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from .core import EntityType, NormalizedEntity, Metadata, PersonName, OrderLine
from .normalizers import DataNormalizer


class DomainParser:
    """Base class for domain-specific parsers."""
    
    def __init__(self):
        self.normalizer = DataNormalizer()
    
    def parse(self, input_text: str, **kwargs) -> NormalizedEntity:
        """Parse input text and return normalized entity."""
        raise NotImplementedError


class InvoiceParser(DomainParser):
    """Parser for invoice data."""
    
    def parse(self, input_text: str, **kwargs) -> NormalizedEntity:
        """Parse invoice text."""
        confidence = 0.9
        transformations = []
        
        # Extract invoice number
        invoice_patterns = [
            r'Invoice\s*#?\s*([A-Z0-9\-]+)',
            r'INV[:\s]*([A-Z0-9\-]+)',
            r'#([A-Z0-9\-]+)'
        ]
        
        invoice_number = None
        for pattern in invoice_patterns:
            match = re.search(pattern, input_text, re.IGNORECASE)
            if match:
                invoice_number = match.group(1)
                break
        
        if not invoice_number:
            confidence -= 0.1
        
        # Extract vendor
        vendor_patterns = [
            r'Vendor:\s*([^|]+)',
            r'From:\s*([^|]+)',
            r'([A-Za-z\s]+(?:Ltd|Inc|Corp|LLC)\.?)'
        ]
        
        vendor_name = None
        for pattern in vendor_patterns:
            match = re.search(pattern, input_text)
            if match:
                vendor_name = match.group(1).strip()
                break
        
        if not vendor_name:
            confidence -= 0.15
        
        # Extract date
        date_pattern = r'Date:\s*([0-9\/\-\.]+)'
        date_match = re.search(date_pattern, input_text)
        
        invoice_date = None
        if date_match:
            try:
                invoice_date, _ = self.normalizer.normalize_date(date_match.group(1))
            except ValueError:
                confidence -= 0.1
        
        # Extract total and currency
        total_patterns = [
            r'Total:\s*([£€$¥]?[\d,]+\.?\d*)',
            r'Amount:\s*([£€$¥]?[\d,]+\.?\d*)',
            r'([£€$¥][\d,]+\.?\d*)'
        ]
        
        total_amount = None
        currency_code = None
        
        for pattern in total_patterns:
            match = re.search(pattern, input_text)
            if match:
                try:
                    currency_data, _ = self.normalizer.normalize_currency(match.group(1))
                    total_amount = currency_data['amount']
                    currency_code = currency_data.get('currency_code')
                    break
                except ValueError:
                    continue
        
        # Extract tax rate
        tax_match = re.search(r'VAT\s+(\d+)%', input_text)
        tax_rate = float(tax_match.group(1)) if tax_match else None
        
        attributes = {
            "invoice_number": invoice_number,
            "vendor_name": vendor_name,
            "invoice_date": invoice_date,
            "total_amount": total_amount,
            "currency_code": currency_code
        }
        
        if tax_rate:
            attributes["tax_rate_percent"] = tax_rate
        
        # Remove None values
        attributes = {k: v for k, v in attributes.items() if v is not None}
        
        metadata = Metadata(
            confidence=confidence,
            source="text_parser",
            transformations=transformations,
            parser_version="1.0.0"
        )
        
        return NormalizedEntity(
            entity_type=EntityType.INVOICE,
            attributes=attributes,
            metadata=metadata
        )


class AddressParser(DomainParser):
    """Parser for address data."""
    
    def parse(self, input_text: str, **kwargs) -> NormalizedEntity:
        """Parse address text."""
        confidence = 0.9
        
        # Extract person name
        name_pattern = r'(?:Bill To:|To:)?\s*([^,]+(?:\s+[^,]+)*)'
        name_match = re.search(name_pattern, input_text)
        
        person = None
        if name_match:
            full_name = name_match.group(1).strip()
            name_parts = full_name.split()
            
            if len(name_parts) >= 2:
                person = {
                    "given_name": name_parts[0],
                    "family_name": name_parts[-1]
                }
                if len(name_parts) > 2:
                    person["middle_name"] = " ".join(name_parts[1:-1])
        
        # Extract address components
        parts = [part.strip() for part in input_text.split(',')]
        
        street_address = None
        district = None
        city = None
        postal_code = None
        country_name = None
        country_code = None
        
        # Try to parse components
        if len(parts) >= 4:
            # Assuming format: Name, Street, District, City Postal, Country
            street_address = parts[1] if len(parts) > 1 else None
            
            # Extract district if present
            if "dist" in parts[2].lower() or "district" in parts[2].lower():
                district = parts[2]
                city_postal = parts[3] if len(parts) > 3 else ""
                country_name = parts[4] if len(parts) > 4 else ""
            else:
                city_postal = parts[2] if len(parts) > 2 else ""
                country_name = parts[3] if len(parts) > 3 else ""
            
            # Extract city and postal code
            postal_match = re.search(r'(\d{5,6})', city_postal)
            if postal_match:
                postal_code = postal_match.group(1)
                city = city_postal.replace(postal_code, "").strip()
            else:
                city = city_postal.strip()
            
            # Normalize country
            if country_name:
                try:
                    country_code, _ = self.normalizer.normalize_country(country_name.strip())
                except ValueError:
                    confidence -= 0.1
        
        attributes = {
            "street_address": street_address,
            "city": city,
            "country_name": country_name,
            "country_code": country_code
        }
        
        if person:
            attributes["person"] = person
        if district:
            attributes["district"] = district
        if postal_code:
            attributes["postal_code"] = postal_code
        
        # Remove None values
        attributes = {k: v for k, v in attributes.items() if v is not None}
        
        metadata = Metadata(
            confidence=confidence,
            parser_version="1.2.0",
            normalization_ruleset="UPU/CLDR"
        )
        
        return NormalizedEntity(
            entity_type=EntityType.ADDRESS,
            attributes=attributes,
            metadata=metadata
        )


class ContactParser(DomainParser):
    """Parser for contact information."""
    
    def parse(self, input_text: str, **kwargs) -> NormalizedEntity:
        """Parse contact text."""
        confidence = 0.95
        transformations = []
        
        attributes = {}
        
        # Extract phone number
        phone_patterns = [
            r'(\+?\d{1,4}[\s\-\(\)]?\d{2,4}[\s\-\(\)]?\d{2,4}[\s\-]?\d{2,4})',
            r'\((\d{3})\)\s*(\d{3})\-(\d{2})\-(\d{2})'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, input_text)
            if match:
                phone_str = match.group(0)
                try:
                    phone_data, phone_meta = self.normalizer.normalize_phone(phone_str)
                    attributes.update(phone_data)
                    if phone_meta.get("transformations"):
                        transformations.extend(phone_meta["transformations"])
                    break
                except ValueError:
                    continue
        
        # Extract extension
        ext_match = re.search(r'ext\.?\s*(\d+)', input_text, re.IGNORECASE)
        if ext_match:
            attributes["phone_extension"] = ext_match.group(1)
        
        # Extract email
        email_pattern = r'([a-zA-Z0-9._%+-]+(?:\[at\]|@)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_match = re.search(email_pattern, input_text)
        
        if email_match:
            email_str = email_match.group(1)
            try:
                email, email_meta = self.normalizer.normalize_email(email_str)
                attributes["email"] = email
                if email_meta.get("transformations"):
                    transformations.extend(email_meta["transformations"])
            except ValueError:
                confidence -= 0.05
        
        metadata = Metadata(
            confidence=confidence,
            standard="E.164",
            transformations=transformations
        )
        
        return NormalizedEntity(
            entity_type=EntityType.CONTACT,
            attributes=attributes,
            metadata=metadata
        )


class ProductParser(DomainParser):
    """Parser for product information."""
    
    def parse(self, input_text: str, **kwargs) -> NormalizedEntity:
        """Parse product text."""
        confidence = 0.95
        
        attributes = {}
        
        # Extract product name
        name_patterns = [
            r'Name:\s*([^—\-]+)',
            r'^([^—\-]+?)(?:\s*—|\s*\d)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, input_text)
            if match:
                name = match.group(1).strip()
                # Remove weight info from name
                name = re.sub(r'\s*\d+(?:\.\d+)?kg\s*', '', name)
                attributes["name"] = name
                break
        
        # Extract weight
        weight_match = re.search(r'(\d+(?:\.\d+)?)kg', input_text)
        if weight_match:
            attributes["net_weight_kg"] = float(weight_match.group(1))
        
        # Extract price and currency
        price_patterns = [
            r'Price:\s*([€£$¥]?[\d,]+\.?\d*)',
            r'([€£$¥][\d,]+\.?\d*)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, input_text)
            if match:
                try:
                    currency_data, _ = self.normalizer.normalize_currency(match.group(1))
                    attributes["price"] = currency_data['amount']
                    if 'currency_code' in currency_data:
                        attributes["currency_code"] = currency_data['currency_code']
                    break
                except ValueError:
                    continue
        
        # Extract category
        category_pattern = r'Category:\s*([^—\-\n]+)'
        category_match = re.search(category_pattern, input_text)
        if category_match:
            category_str = category_match.group(1).strip()
            # Split by > for hierarchical categories
            categories = [cat.strip() for cat in category_str.split('>')]
            attributes["category_path"] = categories
        
        metadata = Metadata(
            confidence=confidence,
            schema="regex_key_value"
        )
        
        return NormalizedEntity(
            entity_type=EntityType.PRODUCT,
            attributes=attributes,
            metadata=metadata
        )


class PersonParser(DomainParser):
    """Parser for person information."""
    
    def parse(self, input_text: str, **kwargs) -> NormalizedEntity:
        """Parse person text."""
        confidence = 0.95
        transformations = []
        
        attributes = {}
        
        # Extract honorific and name
        name_pattern = r'(Prof\.|Dr\.|Mr\.|Mrs\.|Ms\.)?\s*([^(]+?)(?:\s*\([^)]+\))?'
        name_match = re.search(name_pattern, input_text)
        
        if name_match:
            honorific = name_match.group(1)
            full_name = name_match.group(2).strip()
            
            if honorific:
                attributes["honorific"] = honorific
            
            attributes["full_name"] = full_name
            
            # Create ASCII version if needed
            ascii_name, text_meta = self.normalizer.normalize_text(full_name)
            if text_meta.get("transliteration"):
                attributes["ascii_full_name"] = ascii_name
                transformations.append(text_meta["transliteration"])
        
        # Extract role
        role_pattern = r'\(([^)]+)\)'
        role_match = re.search(role_pattern, input_text)
        if role_match:
            attributes["role"] = role_match.group(1)
        
        # Extract email
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_match = re.search(email_pattern, input_text)
        if email_match:
            attributes["email"] = email_match.group(1)
        
        # Extract phone
        phone_pattern = r'(\+\d{1,4}[\s\-\(\)]?\d{1,4}[\s\-\(\)]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4})'
        phone_match = re.search(phone_pattern, input_text)
        if phone_match:
            try:
                phone_data, phone_meta = self.normalizer.normalize_phone(phone_match.group(1))
                if "phone_e164" in phone_data:
                    attributes["phone_e164"] = phone_data["phone_e164"]
                if "country_code_inferred" in phone_data:
                    attributes["country_code_inferred"] = phone_data["country_code_inferred"]
                
                if phone_meta.get("phone_rules"):
                    transformations.append(phone_meta["phone_rules"])
            except ValueError:
                confidence -= 0.05
        
        metadata = Metadata(
            confidence=confidence,
            transformations=transformations
        )
        
        return NormalizedEntity(
            entity_type=EntityType.PERSON,
            attributes=attributes,
            metadata=metadata
        )