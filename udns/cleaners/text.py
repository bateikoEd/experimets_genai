
"""
Text cleaning utilities for UDNS data cleaning.
"""

import re
import unicodedata
from typing import Any, List, Optional, Dict, Set
from .base import BaseCleaner, CleaningContext, CleanResult, CleaningOperation, CleaningOperationType


class TextCleaner(BaseCleaner):
    """General text cleaner for standardizing text data."""
    
    def __init__(self, remove_extra_spaces: bool = True,
                 normalize_whitespace: bool = True,
                 remove_control_chars: bool = True,
                 normalize_unicode: bool = True,
                 unicode_form: str = "NFC"):
        super().__init__("text_cleaner", "1.0.0")
        self.remove_extra_spaces = remove_extra_spaces
        self.normalize_whitespace = normalize_whitespace
        self.remove_control_chars = remove_control_chars
        self.normalize_unicode = normalize_unicode
        self.unicode_form = unicode_form
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize text data."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Remove control characters
            if self.remove_control_chars:
                old_data = data
                data = ''.join(char for char in data if unicodedata.category(char)[0] != 'C')
                operations.append(CleaningOperation(
                    field=context.field or "text",
                    operation_type=CleaningOperationType.REMOVE,
                    description="Remove control characters",
                    before_value=old_data,
                    after_value=data
                ))
            
            # Normalize Unicode
            if self.normalize_unicode:
                old_data = data
                data = unicodedata.normalize(self.unicode_form, data)
                operations.append(CleaningOperation(
                    field=context.field or "text",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description=f"Normalize Unicode to {self.unicode_form}",
                    before_value=old_data,
                    after_value=data
                ))
            
            # Normalize whitespace
            if self.normalize_whitespace:
                old_data = data
                data = re.sub(r'\s+', ' ', data).strip()
                operations.append(CleaningOperation(
                    field=context.field or "text",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Normalize whitespace",
                    before_value=old_data,
                    after_value=data
                ))
            
            return CleanResult(data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field=context.field or "text",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Text cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if not isinstance(self.remove_extra_spaces, bool):
            errors.append("remove_extra_spaces must be boolean")
        if not isinstance(self.normalize_whitespace, bool):
            errors.append("normalize_whitespace must be boolean")
        if not isinstance(self.remove_control_chars, bool):
            errors.append("remove_control_chars must be boolean")
        if not isinstance(self.normalize_unicode, bool):
            errors.append("normalize_unicode must be boolean")
        if self.unicode_form not in ["NFC", "NFD", "NFKC", "NFKD"]:
            errors.append("unicode_form must be 'NFC', 'NFD', 'NFKC', or 'NFKD'")
        return errors


class PunctuationCleaner(BaseCleaner):
    """Cleaner for standardizing punctuation."""
    
    def __init__(self, preserve_essential: bool = True,
                 standardize_quotes: bool = True,
                 standardize_dashes: bool = True,
                 standardize_ellipsis: bool = True,
                 remove_redundant: bool = True):
        super().__init__("punctuation_cleaner", "1.0.0")
        self.preserve_essential = preserve_essential
        self.standardize_quotes = standardize_quotes
        self.standardize_dashes = standardize_dashes
        self.standardize_ellipsis = standardize_ellipsis
        self.remove_redundant = remove_redundant
        
        # Punctuation mappings
        self.quote_mappings = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '«': '"',
            '»': '"',
            '„': '"',
            '‟': '"',
            '‹': "'",
            '›': "'",
            '「': '"',
            '」': '"',
            '『': '"',
            '』': '"',
            '〝': '"',
            '〞': '"'
        }
        
        self.dash_mappings = {
            '—': '-',
            '–': '-',
            '―': '-',
            '‒': '-',
            '‐': '-',
            '‑': '-',
            '‾': '-',
            '⁓': '-'
        }
        
        self.ellipsis_mappings = {
            '…': '...',
            '⋯': '...',
            '⋮': '...',
            '⋱': '...',
            '⋰': '...'
        }
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize punctuation."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Standardize quotes
            if self.standardize_quotes:
                old_data = data
                for old_quote, new_quote in self.quote_mappings.items():
                    data = data.replace(old_quote, new_quote)
                
                if data != old_data:
                    operations.append(CleaningOperation(
                        field=context.field or "punctuation",
                        operation_type=CleaningOperationType.STANDARDIZE,
                        description="Standardize quotes",
                        before_value=old_data,
                        after_value=data
                    ))
            
            # Standardize dashes
            if self.standardize_dashes:
                old_data = data
                for old_dash, new_dash in self.dash_mappings.items():
                    data = data.replace(old_dash, new_dash)
                
                if data != old_data:
                    operations.append(CleaningOperation(
                        field=context.field or "punctuation",
                        operation_type=CleaningOperationType.STANDARDIZE,
                        description="Standardize dashes",
                        before_value=old_data,
                        after_value=data
                    ))
            
            # Standardize ellipsis
            if self.standardize_ellipsis:
                old_data = data
                for old_ellipsis, new_ellipsis in self.ellipsis_mappings.items():
                    data = data.replace(old_ellipsis, new_ellipsis)
                
                if data != old_data:
                    operations.append(CleaningOperation(
                        field=context.field or "punctuation",
                        operation_type=CleaningOperationType.STANDARDIZE,
                        description="Standardize ellipsis",
                        before_value=old_data,
                        after_value=data
                    ))
            
            # Remove redundant punctuation
            if self.remove_redundant:
                old_data = data
                
                # Remove multiple consecutive punctuation
                data = re.sub(r'([.,!?;:])\1+', r'\1', data)
                
                # Remove punctuation at start/end of string (except essential)
                if not self.preserve_essential:
                    data = data.strip('.,;:!?"\'()[]{}<>')
                
                if data != old_data:
                    operations.append(CleaningOperation(
                        field=context.field or "punctuation",
                        operation_type=CleaningOperationType.REMOVE,
                        description="Remove redundant punctuation",
                        before_value=old_data,
                        after_value=data
                    ))
            
            return CleanResult(data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field=context.field or "punctuation",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Punctuation cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if not isinstance(self.preserve_essential, bool):
            errors.append("preserve_essential must be boolean")
        if not isinstance(self.standardize_quotes, bool):
            errors.append("standardize_quotes must be boolean")
        if not isinstance(self.standardize_dashes, bool):
            errors.append("standardize_dashes must be boolean")
        if not isinstance(self.standardize_ellipsis, bool):
            errors.append("standardize_ellipsis must be boolean")
        if not isinstance(self.remove_redundant, bool):
            errors.append("remove_redundant must be boolean")
        return errors


class CaseCleaner(BaseCleaner):
    """Cleaner for standardizing text case."""
    
    def __init__(self, target_case: str = "sentence",
                 preserve_acronyms: bool = True,
                 min_word_length: int = 3):
        super().__init__("case_cleaner", "1.0.0")
        self.target_case = target_case
        self.preserve_acronyms = preserve_acronyms
        self.min_word_length = min_word_length
        
        # Common acronyms to preserve
        self.common_acronyms = {
            "USA", "UK", "UN", "EU", "NATO", "NASA", "FBI", "CIA", "CEO", "CTO",
            "CFO", "COO", "VP", "MD", "PhD", "BA", "MA", "MSc", "BSc", "LLB",
            "MD", "DO", "RN", "LPN", "CNA", "EKG", "MRI", "CT", "XRAY", "GPS",
            "WiFi", "USB", "HDMI", "LCD", "LED", "TV", "PC", "MAC", "iOS", "Android",
            "API", "SDK", "SQL", "HTML", "HTTP", "HTTPS", "FTP", "TCP", "IP", "DNS"}
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize text case."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            if self.target_case == "sentence":
                data = self._to_sentence_case(data, operations)
            elif self.target_case == "title":
                data = self._to_title_case(data, operations)
            elif self.target_case == "upper":
                data = self._to_upper_case(data, operations)
            elif self.target_case == "lower":
                data = self._to_lower_case(data, operations)
            else:
                raise ValueError(f"Unsupported target_case: {self.target_case}")
            
            return CleanResult(data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field=context.field or "case",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Case cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def _to_sentence_case(self, text: str, operations: List[CleaningOperation]) -> str:
        """Convert text to sentence case."""
        old_text = text
        
        # Handle empty string
        if not text.strip():
            return text
        
        # Convert to lowercase first
        text = text.lower()
        
        # Capitalize first letter of the string
        if text:
            text = text[0].upper() + text[1:]
        
        # Capitalize first letter after sentence-ending punctuation
        text = re.sub(r'([.!?]\s*)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        # Preserve acronyms
        if self.preserve_acronyms:
            for acronym in self.common_acronyms:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(acronym) + r'\b'
                text = re.sub(pattern, acronym, text, flags=re.IGNORECASE)
        
        if text != old_text:
            operations.append(CleaningOperation(
                field=context.field or "case",
                operation_type=CleaningOperationType.STANDARDIZE,
                description="Convert to sentence case",
                before_value=old_text,
                after_value=text
            ))
        
        return text
    
    def _to_title_case(self, text: str, operations: List[CleaningOperation]) -> str:
        """Convert text to title case."""
        old_text = text
        
        # Handle empty string
        if not text.strip():
            return text
        
        # Convert to title case
        text = text.title()
        
        # Preserve acronyms
        if self.preserve_acronyms:
            for acronym in self.common_acronyms:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(acronym) + r'\b'
                text = re.sub(pattern, acronym, text, flags=re.IGNORECASE)
        
        if text != old_text:
            operations.append(CleaningOperation(
                field=context.field or "case",
                operation_type=CleaningOperationType.STANDARDIZE,
                description="Convert to title case",
                before_value=old_text,
                after_value=text
            ))
        
        return text
    
    def _to_upper_case(self, text: str, operations: List[CleaningOperation]) -> str:
        """Convert text to uppercase."""
        old_text = text
        text = text.upper()
        
        if text != old_text:
            operations.append(CleaningOperation(
                field=context.field or "case",
                operation_type=CleaningOperationType.STANDARDIZE,
                description="Convert to uppercase",
                before_value=old_text,
                after_value=text
            ))
        
        return text
    
    def _to_lower_case(self, text: str, operations: List[CleaningOperation]) -> str:
        """Convert text to lowercase."""
        old_text = text
        text = text.lower()
        
        if text != old_text:
            operations.append(CleaningOperation(
                field=context.field or "case",
                operation_type=CleaningOperationType.STANDARDIZE,
                description="Convert to lowercase",
                before_value=old_text,
                after_value=text
            ))
        
        return text
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.target_case not in ["sentence", "title", "upper", "lower"]:
            errors.append("target_case must be 'sentence', 'title', 'upper', or 'lower'")
        if not isinstance(self.preserve_acronyms, bool):
            errors.append("preserve_acronyms must be boolean")
        if not isinstance(self.min_word_length, int) or self.min_word_length < 1:
            errors.append("min_word_length must be a positive integer")
        return errors