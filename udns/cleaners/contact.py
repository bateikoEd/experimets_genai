"""
Contact-specific cleaners for UDNS data cleaning.
"""

import re
from typing import Any, List, Optional, Dict
from .base import BaseCleaner, CleaningContext, CleanResult, CleaningOperation, CleaningOperationType
from ..normalizers import DataNormalizer


class PhoneNumberCleaner(BaseCleaner):
    """Cleaner for standardizing phone numbers."""
    
    def __init__(self, target_format: str = "E.164",
                 validate_format: bool = True,
                 country_hint: Optional[str] = None,
                 remove_extensions: bool = False):
        super().__init__("phone_number_cleaner", "1.0.0")
        self.target_format = target_format
        self.validate_format = validate_format
        self.country_hint = country_hint
        self.remove_extensions = remove_extensions
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize phone numbers."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Extract extension if present
            extension = None
            if not self.remove_extensions:
                ext_match = re.search(r'ext\.?\s*(\d+)', data, re.IGNORECASE)
                if ext_match:
                    extension = ext_match.group(1)
                    operations.append(CleaningOperation(
                        field="phone_number",
                        operation_type=CleaningOperationType.EXTRACT,
                        description="Extract phone extension",
                        before_value=data,
                        after_value=extension
                    ))
            
            # Use DataNormalizer for phone number parsing
            phone_data, meta = DataNormalizer.normalize_phone(data, self.country_hint)
            
            # Format to target format
            if self.target_format == "E.164" and "phone_e164" in phone_data:
                result = phone_data["phone_e164"]
            elif self.target_format == "national" and "phone_national" in phone_data:
                result = phone_data["phone_national"]
            else:
                result = phone_data.get("phone_e164", data)
            
            operations.append(CleaningOperation(
                field="phone_number",
                operation_type=CleaningOperationType.NORMALIZE,
                description=f"Normalize phone number: {meta}",
                before_value=data,
                after_value=result
            ))
            
            # Validate format if requested
            if self.validate_format:
                if not self._is_valid_phone_number(result):
                    operations.append(CleaningOperation(
                        field="phone_number",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Invalid phone number format: {result}",
                        success=False,
                        error_message=f"Invalid phone number format: {result}"
                    ))
                    return CleanResult(original_data, operations, context)
            
            # Add extension back if present
            if extension and not self.remove_extensions:
                result = f"{result} ext.{extension}"
                operations.append(CleaningOperation(
                    field="phone_number",
                    operation_type=CleaningOperationType.COMBINE,
                    description=f"Add extension: {extension}",
                    before_value=result,
                    after_value=f"{result} ext.{extension}"
                ))
            
            return CleanResult(result, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="phone_number",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Phone number cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def _is_valid_phone_number(self, phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False
        
        # Basic E.164 validation
        if phone.startswith('+'):
            # Check if it has a valid country code and number
            if len(phone) < 10 or len(phone) > 15:
                return False
            # Check if the rest are digits
            if not phone[1:].isdigit():
                return False
            return True
        
        # Basic national format validation
        if re.match(r'^\d{3}-\d{3}-\d{4}$', phone):
            return True
        
        if re.match(r'^\(\d{3}\)\s*\d{3}-\d{4}$', phone):
            return True
        
        if re.match(r'^\d{10}$', phone):
            return True
        
        return False
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.target_format not in ["E.164", "national"]:
            errors.append("target_format must be 'E.164' or 'national'")
        if not isinstance(self.validate_format, bool):
            errors.append("validate_format must be boolean")
        if self.country_hint is not None and not isinstance(self.country_hint, str):
            errors.append("country_hint must be string or None")
        if not isinstance(self.remove_extensions, bool):
            errors.append("remove_extensions must be boolean")
        return errors


class EmailCleaner(BaseCleaner):
    """Cleaner for standardizing email addresses."""
    
    def __init__(self, target_format: str = "lowercase",
                 validate_format: bool = True,
                 remove_subaddresses: bool = False,
                 allowed_domains: Optional[List[str]] = None):
        super().__init__("email_cleaner", "1.0.0")
        self.target_format = target_format
        self.validate_format = validate_format
        self.remove_subaddresses = remove_subaddresses
        self.allowed_domains = allowed_domains
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize email addresses."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Use DataNormalizer for email parsing
            normalized_email, meta = DataNormalizer.normalize_email(data)
            
            operations.append(CleaningOperation(
                field="email",
                operation_type=CleaningOperationType.NORMALIZE,
                description=f"Normalize email: {meta}",
                before_value=data,
                after_value=normalized_email
            ))
            
            # Remove subaddresses if requested
            if self.remove_subaddresses:
                old_email = normalized_email
                # Remove +subaddress part
                if '+' in normalized_email:
                    local_part, domain = normalized_email.split('@', 1)
                    local_part = local_part.split('+')[0]
                    normalized_email = f"{local_part}@{domain}"
                    
                    operations.append(CleaningOperation(
                        field="email",
                        operation_type=CleaningOperationType.REMOVE,
                        description="Remove subaddress",
                        before_value=old_email,
                        after_value=normalized_email
                    ))
            
            # Apply target format
            if self.target_format == "lowercase":
                old_email = normalized_email
                normalized_email = normalized_email.lower()
                
                operations.append(CleaningOperation(
                    field="email",
                    operation_type=CleaningOperationType.STANDARDIZE,
                    description="Convert to lowercase",
                    before_value=old_email,
                    after_value=normalized_email
                ))
            
            # Validate format if requested
            if self.validate_format:
                if not self._is_valid_email(normalized_email):
                    operations.append(CleaningOperation(
                        field="email",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Invalid email format: {normalized_email}",
                        success=False,
                        error_message=f"Invalid email format: {normalized_email}"
                    ))
                    return CleanResult(original_data, operations, context)
                
                # Check domain if allowed domains specified
                if self.allowed_domains:
                    domain = normalized_email.split('@')[1]
                    if domain not in self.allowed_domains:
                        operations.append(CleaningOperation(
                            field="email",
                            operation_type=CleaningOperationType.VALIDATE,
                            description=f"Domain not allowed: {domain}",
                            success=False,
                            error_message=f"Domain not allowed: {domain}"
                        ))
                        return CleanResult(original_data, operations, context)
            
            return CleanResult(normalized_email, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="email",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Email cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        
        # Basic email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.target_format not in ["lowercase", "original"]:
            errors.append("target_format must be 'lowercase' or 'original'")
        if not isinstance(self.validate_format, bool):
            errors.append("validate_format must be boolean")
        if not isinstance(self.remove_subaddresses, bool):
            errors.append("remove_subaddresses must be boolean")
        if self.allowed_domains is not None and not isinstance(self.allowed_domains, list):
            errors.append("allowed_domains must be list or None")
        return errors


class ContactNameCleaner(BaseCleaner):
    """Cleaner for standardizing contact names."""
    
    def __init__(self, target_format: str = "title_case",
                 remove_suffixes: bool = True,
                 standardize_titles: bool = True,
                 allowed_suffixes: Optional[List[str]] = None,
                 allowed_titles: Optional[List[str]] = None):
        super().__init__("contact_name_cleaner", "1.0.0")
        self.target_format = target_format
        self.remove_suffixes = remove_suffixes
        self.standardize_titles = standardize_titles
        self.allowed_suffixes = allowed_suffixes or ["Jr", "Sr", "II", "III", "IV", "V"]
        self.allowed_titles = allowed_titles or ["Mr", "Mrs", "Ms", "Miss", "Dr", "Prof"]
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize contact names."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Parse name components
            name_parts = self._parse_name(data)
            
            # Standardize titles
            if self.standardize_titles and name_parts.get('title'):
                old_title = name_parts['title']
                name_parts['title'] = self._standardize_title(name_parts['title'])
                
                operations.append(CleaningOperation(
                    field="contact_name",
                    operation_type=CleaningOperationType.STANDARDIZE,
                    description=f"Standardize title: {old_title} -> {name_parts['title']}",
                    before_value=old_title,
                    after_value=name_parts['title']
                ))
            
            # Remove suffixes
            if self.remove_suffixes and name_parts.get('suffix'):
                old_suffix = name_parts['suffix']
                name_parts['suffix'] = None
                
                operations.append(CleaningOperation(
                    field="contact_name",
                    operation_type=CleaningOperationType.REMOVE,
                    description=f"Remove suffix: {old_suffix}",
                    before_value=old_suffix,
                    after_value=None
                ))
            
            # Format to target format
            if self.target_format == "title_case":
                formatted_name = self._format_title_case(name_parts)
            elif self.target_format == "last_first":
                formatted_name = self._format_last_first(name_parts)
            elif self.target_format == "full":
                formatted_name = self._format_full(name_parts)
            else:
                formatted_name = self._format_standard(name_parts)
            
            operations.append(CleaningOperation(
                field="contact_name",
                operation_type=CleaningOperationType.FORMAT,
                description=f"Format to {self.target_format}",
                before_value=data,
                after_value=formatted_name
            ))
            
            return CleanResult(formatted_name, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="contact_name",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Contact name cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def _parse_name(self, name: str) -> Dict[str, Optional[str]]:
        """Parse name into components."""
        name = name.strip()
        parts = name.split()
        
        result = {
            'title': None,
            'first': None,
            'middle': None,
            'last': None,
            'suffix': None
        }
        
        if not parts:
            return result
        
        # Check for title
        if parts[0].endswith('.'):
            result['title'] = parts[0]
            parts = parts[1:]
        
        if not parts:
            return result
        
        # Check for suffix
        if len(parts) > 1 and parts[-1].upper() in [s.upper() for s in self.allowed_suffixes]:
            result['suffix'] = parts[-1]
            parts = parts[:-1]
        
        if not parts:
            return result
        
        # Split first, middle, last names
        if len(parts) == 1:
            result['first'] = parts[0]
        elif len(parts) == 2:
            result['first'] = parts[0]
            result['last'] = parts[1]
        else:
            result['first'] = parts[0]
            result['middle'] = ' '.join(parts[1:-1])
            result['last'] = parts[-1]
        
        return result
    
    def _standardize_title(self, title: str) -> str:
        """Standardize title abbreviations."""
        title_map = {
            'Mr.': 'Mr',
            'Mrs.': 'Mrs',
            'Ms.': 'Ms',
            'Miss': 'Miss',
            'Dr.': 'Dr',
            'Prof.': 'Prof'
        }
        
        return title_map.get(title, title)
    
    def _format_title_case(self, name_parts: Dict[str, Optional[str]]) -> str:
        """Format name in title case."""
        parts = []
        
        if name_parts['title']:
            parts.append(name_parts['title'])
        
        if name_parts['first']:
            parts.append(name_parts['first'].title())
        
        if name_parts['middle']:
            parts.append(name_parts['middle'].title())
        
        if name_parts['last']:
            parts.append(name_parts['last'].title())
        
        if name_parts['suffix']:
            parts.append(name_parts['suffix'])
        
        return ' '.join(parts)
    
    def _format_last_first(self, name_parts: Dict[str, Optional[str]]) -> str:
        """Format name as Last, First."""
        parts = []
        
        if name_parts['last']:
            parts.append(name_parts['last'])
        
        if name_parts['first']:
            parts.append(name_parts['first'])
        
        if name_parts['middle']:
            parts.append(name_parts['middle'])
        
        if name_parts['suffix']:
            parts.append(name_parts['suffix'])
        
        return ', '.join(parts)
    
    def _format_full(self, name_parts: Dict[str, Optional[str]]) -> str:
        """Format name in full format."""
        return self._format_title_case(name_parts)
    
    def _format_standard(self, name_parts: Dict[str, Optional[str]]) -> str:
        """Format name in standard format."""
        return self._format_title_case(name_parts)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.target_format not in ["title_case", "last_first", "full", "standard"]:
            errors.append("target_format must be 'title_case', 'last_first', 'full', or 'standard'")
        if not isinstance(self.remove_suffixes, bool):
            errors.append("remove_suffixes must be boolean")
        if not isinstance(self.standardize_titles, bool):
            errors.append("standardize_titles must be boolean")
        if self.allowed_suffixes is not None and not isinstance(self.allowed_suffixes, list):
            errors.append("allowed_suffixes must be list or None")
        if self.allowed_titles is not None and not isinstance(self.allowed_titles, list):
            errors.append("allowed_titles must be list or None")
        return errors


class ContactOrganizationCleaner(BaseCleaner):
    """Cleaner for standardizing contact organization names."""
    
    def __init__(self, remove_suffixes: bool = True,
                 standardize_case: bool = True,
                 allowed_suffixes: Optional[List[str]] = None,
                 target_case: str = "title"):
        super().__init__("contact_organization_cleaner", "1.0.0")
        self.remove_suffixes = remove_suffixes
        self.standardize_case = standardize_case
        self.allowed_suffixes = allowed_suffixes or ["Inc", "Ltd", "Corp", "LLC", "GmbH", "S.A.", "Pty Ltd"]
        self.target_case = target_case
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize contact organization names."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Remove suffixes
            if self.remove_suffixes:
                for suffix in self.allowed_suffixes:
                    if data.endswith(suffix):
                        old_data = data
                        data = data[:-len(suffix)].strip()
                        operations.append(CleaningOperation(
                            field="organization_name",
                            operation_type=CleaningOperationType.REMOVE,
                            description=f"Remove suffix '{suffix}'",
                            before_value=old_data,
                            after_value=data
                        ))
                        break
            
            # Standardize case
            if self.standardize_case:
                old_data = data
                if self.target_case == "title":
                    data = data.title()
                elif self.target_case == "upper":
                    data = data.upper()
                elif self.target_case == "lower":
                    data = data.lower()
                
                operations.append(CleaningOperation(
                    field="organization_name",
                    operation_type=CleaningOperationType.STANDARDIZE,
                    description=f"Convert to {self.target_case} case",
                    before_value=old_data,
                    after_value=data
                ))
            
            # Remove extra spaces
            old_data = data
            data = re.sub(r'\s+', ' ', data).strip()
            operations.append(CleaningOperation(
                field="organization_name",
                operation_type=CleaningOperationType.NORMALIZE,
                description="Remove extra spaces",
                before_value=old_data,
                after_value=data
            ))
            
            return CleanResult(data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="organization_name",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Contact organization cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if not isinstance(self.remove_suffixes, bool):
            errors.append("remove_suffixes must be boolean")
        if not isinstance(self.standardize_case, bool):
            errors.append("standardize_case must be boolean")
        if self.allowed_suffixes is not None and not isinstance(self.allowed_suffixes, list):
            errors.append("allowed_suffixes must be list or None")
        if self.target_case not in ["title", "upper", "lower"]:
            errors.append("target_case must be 'title', 'upper', or 'lower'")
        return errors