"""
Invoice-specific cleaners for UDNS data cleaning.
"""

import re
from typing import Any, List, Optional, Dict, Union
from .base import BaseCleaner, CleaningContext, CleanResult, CleaningOperation, CleaningOperationType
from ..normalizers import DataNormalizer


class InvoiceNumberCleaner(BaseCleaner):
    """Cleaner for standardizing invoice numbers."""
    
    def __init__(self, remove_prefixes: bool = True,
                 remove_suffixes: bool = True,
                 standardize_format: bool = True,
                 allowed_prefixes: Optional[List[str]] = None,
                 allowed_suffixes: Optional[List[str]] = None):
        super().__init__("invoice_number_cleaner", "1.0.0")
        self.remove_prefixes = remove_prefixes
        self.remove_suffixes = remove_suffixes
        self.standardize_format = standardize_format
        self.allowed_prefixes = allowed_prefixes or ["INV", "INVOICE", "BILL", "RECEIPT"]
        self.allowed_suffixes = allowed_suffixes or []
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize invoice numbers."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Strip whitespace first
            old_data = data
            data = data.strip()
            if data != old_data:
                operations.append(CleaningOperation(
                    field="invoice_number",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Remove leading/trailing whitespace",
                    before_value=old_data,
                    after_value=data
                ))
            
            # Remove prefixes
            if self.remove_prefixes:
                for prefix in self.allowed_prefixes:
                    if data.startswith(prefix):
                        old_data = data
                        data = data[len(prefix):].strip()
                        operations.append(CleaningOperation(
                            field="invoice_number",
                            operation_type=CleaningOperationType.NORMALIZE,
                            description=f"Remove prefix '{prefix}'",
                            before_value=old_data,
                            after_value=data
                        ))
                        break
            
            # Remove suffixes
            if self.remove_suffixes:
                for suffix in self.allowed_suffixes:
                    if data.endswith(suffix):
                        old_data = data
                        data = data[:-len(suffix)].strip()
                        operations.append(CleaningOperation(
                            field="invoice_number",
                            operation_type=CleaningOperationType.NORMALIZE,
                            description=f"Remove suffix '{suffix}'",
                            before_value=old_data,
                            after_value=data
                        ))
                        break
            
            # Standardize format
            if self.standardize_format:
                old_data = data
                # Remove common separators and normalize
                data = re.sub(r'[^\w\-]', '', data).upper()
                operations.append(CleaningOperation(
                    field="invoice_number",
                    operation_type=CleaningOperationType.STANDARDIZE,
                    description="Standardize format (alphanumeric, uppercase)",
                    before_value=old_data,
                    after_value=data
                ))
            
            return CleanResult(data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="invoice_number",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Invoice number cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if not isinstance(self.remove_prefixes, bool):
            errors.append("remove_prefixes must be boolean")
        if not isinstance(self.remove_suffixes, bool):
            errors.append("remove_suffixes must be boolean")
        if not isinstance(self.standardize_format, bool):
            errors.append("standardize_format must be boolean")
        if self.allowed_prefixes is not None and not isinstance(self.allowed_prefixes, list):
            errors.append("allowed_prefixes must be list or None")
        if self.allowed_suffixes is not None and not isinstance(self.allowed_suffixes, list):
            errors.append("allowed_suffixes must be list or None")
        return errors


class InvoiceAmountCleaner(BaseCleaner):
    """Cleaner for standardizing invoice amounts."""
    
    def __init__(self, remove_currency_symbols: bool = True,
                 standardize_decimals: bool = True,
                 min_amount: Optional[float] = None,
                 max_amount: Optional[float] = None):
        super().__init__("invoice_amount_cleaner", "1.0.0")
        self.remove_currency_symbols = remove_currency_symbols
        self.standardize_decimals = standardize_decimals
        self.min_amount = min_amount
        self.max_amount = max_amount
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize invoice amounts."""
        if isinstance(data, (int, float)):
            return self._clean_numeric_amount(data, context)
        
        if isinstance(data, str):
            return self._clean_string_amount(data, context)
        
        # Non-amount data, return as-is
        return CleanResult(data, [], context)
    
    def _clean_numeric_amount(self, amount: Union[int, float], context: CleaningContext) -> CleanResult:
        """Clean numeric amounts."""
        original_amount = amount
        operations = []
        
        try:
            # Check bounds
            if self.min_amount is not None and amount < self.min_amount:
                operations.append(CleaningOperation(
                    field="invoice_amount",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Amount {amount} below minimum {self.min_amount}",
                    success=False,
                    error_message=f"Amount below minimum: {amount} < {self.min_amount}"
                ))
                return CleanResult(original_amount, operations, context)
            
            if self.max_amount is not None and amount > self.max_amount:
                operations.append(CleaningOperation(
                    field="invoice_amount",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Amount {amount} above maximum {self.max_amount}",
                    success=False,
                    error_message=f"Amount above maximum: {amount} > {self.max_amount}"
                ))
                return CleanResult(original_amount, operations, context)
            
            # Standardize decimals
            if self.standardize_decimals:
                old_amount = amount
                amount = round(float(amount), 2)
                operations.append(CleaningOperation(
                    field="invoice_amount",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Round to 2 decimal places",
                    before_value=old_amount,
                    after_value=amount
                ))
            
            return CleanResult(amount, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="invoice_amount",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Invoice amount cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_amount, [error_op], context)
    
    def _clean_string_amount(self, amount_str: str, context: CleaningContext) -> CleanResult:
        """Clean string amounts."""
        original_amount = amount_str
        operations = []
        
        try:
            # Use DataNormalizer for currency parsing
            currency_data, meta = DataNormalizer.normalize_currency(amount_str)
            amount = currency_data['amount']
            
            operations.append(CleaningOperation(
                field="invoice_amount",
                operation_type=CleaningOperationType.NORMALIZE,
                description=f"Parse currency: {meta}",
                before_value=original_amount,
                after_value=amount
            ))
            
            # Check bounds
            if self.min_amount is not None and amount < self.min_amount:
                operations.append(CleaningOperation(
                    field="invoice_amount",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Amount {amount} below minimum {self.min_amount}",
                    success=False,
                    error_message=f"Amount below minimum: {amount} < {self.min_amount}"
                ))
                return CleanResult(original_amount, operations, context)
            
            if self.max_amount is not None and amount > self.max_amount:
                operations.append(CleaningOperation(
                    field="invoice_amount",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Amount {amount} above maximum {self.max_amount}",
                    success=False,
                    error_message=f"Amount above maximum: {amount} > {self.max_amount}"
                ))
                return CleanResult(original_amount, operations, context)
            
            # Standardize decimals
            if self.standardize_decimals:
                old_amount = amount
                amount = round(amount, 2)
                operations.append(CleaningOperation(
                    field="invoice_amount",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Round to 2 decimal places",
                    before_value=old_amount,
                    after_value=amount
                ))
            
            return CleanResult(amount, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="invoice_amount",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Invoice amount cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_amount, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if not isinstance(self.remove_currency_symbols, bool):
            errors.append("remove_currency_symbols must be boolean")
        if not isinstance(self.standardize_decimals, bool):
            errors.append("standardize_decimals must be boolean")
        if self.min_amount is not None and not isinstance(self.min_amount, (int, float)):
            errors.append("min_amount must be numeric or None")
        if self.max_amount is not None and not isinstance(self.max_amount, (int, float)):
            errors.append("max_amount must be numeric or None")
        if self.min_amount is not None and self.max_amount is not None and self.min_amount >= self.max_amount:
            errors.append("min_amount must be less than max_amount")
        return errors


class InvoiceDateCleaner(BaseCleaner):
    """Cleaner for standardizing invoice dates."""
    
    def __init__(self, target_format: str = "ISO_8601",
                 allow_future: bool = True,
                 allow_past: bool = True,
                 min_date: Optional[str] = None,
                 max_date: Optional[str] = None):
        super().__init__("invoice_date_cleaner", "1.0.0")
        self.target_format = target_format
        self.allow_future = allow_future
        self.allow_past = allow_past
        self.min_date = min_date
        self.max_date = max_date
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize invoice dates."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Use DataNormalizer for date parsing
            normalized_date, meta = DataNormalizer.normalize_date(data)
            
            operations.append(CleaningOperation(
                field="invoice_date",
                operation_type=CleaningOperationType.NORMALIZE,
                description=f"Parse date: {meta}",
                before_value=original_data,
                after_value=normalized_date
            ))
            
            # Check date bounds
            if self.min_date:
                min_dt = datetime.fromisoformat(self.min_date)
                invoice_dt = datetime.fromisoformat(normalized_date)
                if invoice_dt < min_dt:
                    operations.append(CleaningOperation(
                        field="invoice_date",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Date {normalized_date} before minimum {self.min_date}",
                        success=False,
                        error_message=f"Date before minimum: {normalized_date} < {self.min_date}"
                    ))
                    return CleanResult(original_data, operations, context)
            
            if self.max_date:
                max_dt = datetime.fromisoformat(self.max_date)
                invoice_dt = datetime.fromisoformat(normalized_date)
                if invoice_dt > max_dt:
                    operations.append(CleaningOperation(
                        field="invoice_date",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Date {normalized_date} after maximum {self.max_date}",
                        success=False,
                        error_message=f"Date after maximum: {normalized_date} > {self.max_date}"
                    ))
                    return CleanResult(original_data, operations, context)
            
            # Format to target format
            if self.target_format != "ISO_8601":
                old_date = normalized_date
                invoice_dt = datetime.fromisoformat(normalized_date)
                if self.target_format == "timestamp":
                    normalized_date = str(invoice_dt.timestamp())
                else:
                    normalized_date = invoice_dt.strftime(self.target_format)
                
                operations.append(CleaningOperation(
                    field="invoice_date",
                    operation_type=CleaningOperationType.FORMAT,
                    description=f"Format to {self.target_format}",
                    before_value=old_date,
                    after_value=normalized_date
                ))
            
            return CleanResult(normalized_date, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="invoice_date",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Invoice date cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if not isinstance(self.target_format, str):
            errors.append("target_format must be string")
        if not isinstance(self.allow_future, bool):
            errors.append("allow_future must be boolean")
        if not isinstance(self.allow_past, bool):
            errors.append("allow_past must be boolean")
        if self.min_date is not None and not isinstance(self.min_date, str):
            errors.append("min_date must be string or None")
        if self.max_date is not None and not isinstance(self.max_date, str):
            errors.append("max_date must be string or None")
        return errors


class InvoiceVendorCleaner(BaseCleaner):
    """Cleaner for standardizing vendor names."""
    
    def __init__(self, remove_suffixes: bool = True,
                 standardize_case: bool = True,
                 allowed_suffixes: Optional[List[str]] = None,
                 target_case: str = "title"):
        super().__init__("invoice_vendor_cleaner", "1.0.0")
        self.remove_suffixes = remove_suffixes
        self.standardize_case = standardize_case
        self.allowed_suffixes = allowed_suffixes or ["Ltd", "Inc", "Corp", "LLC", "GmbH", "S.A.", "Pty Ltd"]
        self.target_case = target_case
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize vendor names."""
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
                            field="vendor_name",
                            operation_type=CleaningOperationType.NORMALIZE,
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
                    field="vendor_name",
                    operation_type=CleaningOperationType.STANDARDIZE,
                    description=f"Convert to {self.target_case} case",
                    before_value=old_data,
                    after_value=data
                ))
            
            return CleanResult(data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="vendor_name",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Vendor name cleaning failed: {str(e)}",
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