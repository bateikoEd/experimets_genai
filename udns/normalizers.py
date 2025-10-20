"""
Data type normalizers for UDNS specification.
Implements normalization for ISO standards and common data formats.
"""

import re
import unicodedata
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
import phonenumbers
from phonenumbers import NumberParseException


class DataNormalizer:
    """Main data normalizer implementing UDNS standards."""
    
    # ISO 3166-1 alpha-3 country codes mapping
    COUNTRY_CODES = {
        "US": "USA", "GB": "GBR", "UA": "UKR", "VN": "VNM", 
        "DE": "DEU", "FR": "FRA", "JP": "JPN", "CN": "CHN"
    }
    
    # Currency symbol to ISO 4217 mapping
    CURRENCY_SYMBOLS = {
        "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY",
        "₴": "UAH", "₽": "RUB", "¢": "USD"
    }
    
    @staticmethod
    def normalize_date(date_str: str, locale_hint: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Normalize date string to ISO 8601 format.
        
        Args:
            date_str: Input date string
            locale_hint: Optional locale hint for parsing
            
        Returns:
            Tuple of (normalized_date, metadata)
        """
        metadata = {"standard": "ISO 8601"}
        
        # Remove common separators and normalize
        clean_date = re.sub(r'[\/\-\.]', '-', date_str.strip())
        
        # Try different date patterns
        patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY or MM-DD-YYYY
            r'(\d{1,2})\/(\d{1,2})\/(\d{4})', # MM/DD/YYYY or DD/MM/YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, clean_date)
            if match:
                parts = [int(x) for x in match.groups()]
                
                # Determine order based on locale or values
                if len(str(parts[0])) == 4:  # YYYY-MM-DD
                    year, month, day = parts
                elif locale_hint and locale_hint.startswith('en-US'):  # MM-DD-YYYY
                    month, day, year = parts
                else:  # DD-MM-YYYY (default)
                    day, month, year = parts
                
                try:
                    normalized = f"{year:04d}-{month:02d}-{day:02d}"
                    # Validate the date
                    datetime.strptime(normalized, "%Y-%m-%d")
                    return normalized, metadata
                except ValueError:
                    continue
        
        raise ValueError(f"Could not parse date: {date_str}")
    
    @staticmethod
    def normalize_datetime(datetime_str: str, timezone_hint: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Normalize datetime string to ISO 8601 format with timezone.
        
        Args:
            datetime_str: Input datetime string
            timezone_hint: Optional timezone hint
            
        Returns:
            Tuple of (normalized_datetime, metadata)
        """
        metadata = {"standard": "ISO 8601"}
        
        # Extract timezone information
        tz_patterns = [
            r'([+-]\d{2}:?\d{2})$',  # +03:00 or +0300
            r'(UTC|GMT)$',
            r'([A-Z]{3,4})$',  # JST, PST, etc.
        ]
        
        timezone_info = None
        clean_dt = datetime_str.strip()
        
        for pattern in tz_patterns:
            match = re.search(pattern, clean_dt)
            if match:
                timezone_info = match.group(1)
                clean_dt = clean_dt[:match.start()].strip()
                metadata["timezone_source"] = "explicit_" + timezone_info
                break
        
        # Parse date and time components
        dt_pattern = r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?'
        match = re.search(dt_pattern, clean_dt)
        
        if not match:
            raise ValueError(f"Could not parse datetime: {datetime_str}")
        
        year, month, day, hour, minute, second = match.groups()
        second = second or "00"
        
        # Format as ISO 8601
        iso_dt = f"{year}-{month:0>2}-{day:0>2}T{hour:0>2}:{minute}:{second}"
        
        # Add timezone
        if timezone_info:
            if timezone_info in ["UTC", "GMT"]:
                iso_dt += "Z"
            elif timezone_info.startswith(('+', '-')):
                # Normalize timezone format
                tz_clean = re.sub(r'([+-]\d{2})(\d{2})', r'\1:\2', timezone_info)
                iso_dt += tz_clean
            else:
                # Named timezone (approximate)
                tz_offsets = {"JST": "+09:00", "PST": "-08:00", "EST": "-05:00"}
                iso_dt += tz_offsets.get(timezone_info, "+00:00")
        else:
            iso_dt += "Z"  # Default to UTC
        
        return iso_dt, metadata
    
    @staticmethod
    def normalize_phone(phone_str: str, country_hint: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Normalize phone number to E.164 format.
        
        Args:
            phone_str: Input phone string
            country_hint: Optional country code hint
            
        Returns:
            Tuple of (normalized_phone, metadata)
        """
        metadata = {"standard": "E.164"}
        
        # Clean input
        clean_phone = re.sub(r'[^\d+]', '', phone_str)
        
        # Extract extension if present
        extension_match = re.search(r'ext\.?\s*(\d+)', phone_str, re.IGNORECASE)
        extension = extension_match.group(1) if extension_match else None
        
        try:
            # Try to parse with phonenumbers library
            if country_hint:
                parsed = phonenumbers.parse(clean_phone, country_hint)
            else:
                parsed = phonenumbers.parse(clean_phone, None)
            
            if phonenumbers.is_valid_number(parsed):
                e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                
                result = {"phone_e164": e164}
                if extension:
                    result["phone_extension"] = extension
                    metadata["transformations"] = ["extract_extension"]
                
                # Infer country
                country_code = phonenumbers.region_code_for_number(parsed)
                if country_code:
                    iso3_country = DataNormalizer.COUNTRY_CODES.get(country_code, country_code)
                    result["country_code_inferred"] = iso3_country
                
                return result, metadata
                
        except NumberParseException:
            pass
        
        # Fallback: manual parsing
        if clean_phone.startswith('+'):
            return {"phone_e164": clean_phone}, metadata
        
        raise ValueError(f"Could not parse phone number: {phone_str}")
    
    @staticmethod
    def normalize_currency(amount_str: str, currency_hint: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Normalize currency amount and code.
        
        Args:
            amount_str: Amount string with optional currency symbol
            currency_hint: Optional currency code hint
            
        Returns:
            Tuple of (normalized_currency, metadata)
        """
        metadata = {"standard": "ISO 4217"}
        
        # Extract currency symbol or code
        currency_pattern = r'([€£$¥₴₽¢])|([A-Z]{3})'
        currency_match = re.search(currency_pattern, amount_str)
        
        currency_code = None
        if currency_match:
            symbol = currency_match.group(1)
            code = currency_match.group(2)
            
            if symbol:
                currency_code = DataNormalizer.CURRENCY_SYMBOLS.get(symbol)
            elif code:
                currency_code = code
        elif currency_hint:
            currency_code = currency_hint
        
        # Extract numeric amount
        amount_pattern = r'([\d,]+\.?\d*)'
        amount_match = re.search(amount_pattern, amount_str)
        
        if not amount_match:
            raise ValueError(f"Could not extract amount from: {amount_str}")
        
        amount_clean = amount_match.group(1).replace(',', '')
        amount = float(amount_clean)
        
        result = {"amount": amount}
        if currency_code:
            result["currency_code"] = currency_code
        
        # Add minor units for common currencies
        minor_units = {"JPY": 0, "USD": 2, "EUR": 2, "GBP": 2}
        if currency_code in minor_units:
            exponent = minor_units[currency_code]
            result["amount_in_minor_units"] = int(amount * (10 ** exponent))
            metadata["minor_unit_exponent"] = exponent
        
        return result, metadata
    
    @staticmethod
    def normalize_country(country_str: str) -> Tuple[str, Dict[str, Any]]:
        """
        Normalize country name to ISO 3166-1 alpha-3 code.
        
        Args:
            country_str: Country name or code
            
        Returns:
            Tuple of (country_code, metadata)
        """
        metadata = {"standard": "ISO 3166-1 alpha-3"}
        
        # Country name mappings
        country_names = {
            "united states": "USA", "usa": "USA", "us": "USA",
            "united kingdom": "GBR", "uk": "GBR", "britain": "GBR",
            "ukraine": "UKR", "vietnam": "VNM", "germany": "DEU",
            "france": "FRA", "japan": "JPN", "china": "CHN"
        }
        
        clean_country = country_str.lower().strip()
        
        # Direct lookup
        if clean_country in country_names:
            return country_names[clean_country], metadata
        
        # Check if already ISO 3166-1 alpha-3
        if len(country_str) == 3 and country_str.upper() in DataNormalizer.COUNTRY_CODES.values():
            return country_str.upper(), metadata
        
        # Check if ISO 3166-1 alpha-2
        if len(country_str) == 2 and country_str.upper() in DataNormalizer.COUNTRY_CODES:
            return DataNormalizer.COUNTRY_CODES[country_str.upper()], metadata
        
        raise ValueError(f"Could not normalize country: {country_str}")
    
    @staticmethod
    def normalize_email(email_str: str) -> Tuple[str, Dict[str, Any]]:
        """
        Normalize email address.
        
        Args:
            email_str: Email string
            
        Returns:
            Tuple of (normalized_email, metadata)
        """
        metadata = {"standard": "RFC 5322"}
        
        # Replace [at] with @
        clean_email = email_str.replace("[at]", "@").replace(" at ", "@")
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, clean_email):
            if "[at]" in email_str:
                metadata["transformations"] = ["replace_[at]_with_@"]
            return clean_email.lower(), metadata
        
        raise ValueError(f"Invalid email format: {email_str}")
    
    @staticmethod
    def normalize_text(text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Normalize text using Unicode NFKD and strip accents.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (normalized_text, metadata)
        """
        metadata = {}
        
        # Unicode normalization
        normalized = unicodedata.normalize('NFKD', text)
        
        # Strip accents for ASCII version
        ascii_version = ''.join(
            c for c in normalized 
            if unicodedata.category(c) != 'Mn'
        )
        
        if ascii_version != text:
            metadata["transliteration"] = "NFKD_strip_accents"
            return ascii_version, metadata
        
        return text, metadata