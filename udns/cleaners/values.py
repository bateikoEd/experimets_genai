"""
Value cleaning utilities for UDNS data cleaning.
"""

import re
from typing import Any, List, Optional, Union
from decimal import Decimal, InvalidOperation
from datetime import datetime
from .base import BaseCleaner, CleaningContext, CleanResult, CleaningOperation, CleaningOperationType
from ..normalizers import DataNormalizer


class NumericCleaner(BaseCleaner):
    """Cleaner for standardizing numeric values."""
    
    def __init__(self, decimal_places: Optional[int] = None,
                 remove_thousands_separators: bool = True,
                 scientific_notation: bool = False,
                 allow_negative: bool = True,
                 min_value: Optional[float] = None,
                 max_value: Optional[float] = None):
        super().__init__("numeric_cleaner", "1.0.0")
        self.decimal_places = decimal_places
        self.remove_thousands_separators = remove_thousands_separators
        self.scientific_notation = scientific_notation
        self.allow_negative = allow_negative
        self.min_value = min_value
        self.max_value = max_value
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize numeric values."""
        if isinstance(data, (int, float)):
            return self._clean_numeric(data, context)
        
        if isinstance(data, str):
            return self._clean_numeric_string(data, context)
        
        # Non-numeric data, return as-is
        return CleanResult(data, [], context)
    
    def _clean_numeric(self, value: Union[int, float], context: CleaningContext) -> CleanResult:
        """Clean numeric values."""
        original_value = value
        operations = []
        
        try:
            # Check bounds
            if self.min_value is not None and value < self.min_value:
                operations.append(CleaningOperation(
                    field="numeric",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Value {value} below minimum {self.min_value}",
                    success=False,
                    error_message=f"Value below minimum: {value} < {self.min_value}"
                ))
                return CleanResult(original_value, operations, context)
            
            if self.max_value is not None and value > self.max_value:
                operations.append(CleaningOperation(
                    field="numeric",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Value {value} above maximum {self.max_value}",
                    success=False,
                    error_message=f"Value above maximum: {value} > {self.max_value}"
                ))
                return CleanResult(original_value, operations, context)
            
            # Apply decimal places
            if self.decimal_places is not None:
                value = round(float(value), self.decimal_places)
                operations.append(CleaningOperation(
                    field="numeric",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description=f"Round to {self.decimal_places} decimal places",
                    before_value=original_value,
                    after_value=value
                ))
            
            return CleanResult(value, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="numeric",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Numeric cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_value, [error_op], context)
    
    def _clean_numeric_string(self, value: str, context: CleaningContext) -> CleanResult:
        """Clean numeric strings."""
        original_value = value
        operations = []
        
        try:
            # Remove thousands separators
            if self.remove_thousands_separators:
                old_value = value
                value = value.replace(',', '').replace('.', '')
                operations.append(CleaningOperation(
                    field="numeric_string",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Remove thousands separators",
                    before_value=old_value,
                    after_value=value
                ))
            
            # Handle scientific notation
            if self.scientific_notation and 'e' in value.lower():
                try:
                    numeric_value = float(value)
                except ValueError:
                    # Try to parse scientific notation manually
                    match = re.match(r'^([+-]?\d*\.?\d+)[eE]([+-]?\d+)$', value)
                    if match:
                        base = float(match.group(1))
                        exponent = int(match.group(2))
                        numeric_value = base * (10 ** exponent)
                    else:
                        raise ValueError(f"Invalid scientific notation: {value}")
            else:
                # Regular number parsing
                numeric_value = float(value)
            
            # Check if negative is allowed
            if not self.allow_negative and numeric_value < 0:
                operations.append(CleaningOperation(
                    field="numeric_string",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Negative value not allowed: {numeric_value}",
                    success=False,
                    error_message="Negative values not allowed"
                ))
                return CleanResult(original_value, operations, context)
            
            # Apply decimal places
            if self.decimal_places is not None:
                numeric_value = round(numeric_value, self.decimal_places)
                operations.append(CleaningOperation(
                    field="numeric_string",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description=f"Round to {self.decimal_places} decimal places",
                    before_value=numeric_value,
                    after_value=round(numeric_value, self.decimal_places)
                ))
            
            # Check bounds
            if self.min_value is not None and numeric_value < self.min_value:
                operations.append(CleaningOperation(
                    field="numeric_string",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Value {numeric_value} below minimum {self.min_value}",
                    success=False,
                    error_message=f"Value below minimum: {numeric_value} < {self.min_value}"
                ))
                return CleanResult(original_value, operations, context)
            
            if self.max_value is not None and numeric_value > self.max_value:
                operations.append(CleaningOperation(
                    field="numeric_string",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Value {numeric_value} above maximum {self.max_value}",
                    success=False,
                    error_message=f"Value above maximum: {numeric_value} > {self.max_value}"
                ))
                return CleanResult(original_value, operations, context)
            
            return CleanResult(numeric_value, operations, context)
            
        except (ValueError, InvalidOperation) as e:
            error_op = CleaningOperation(
                field="numeric_string",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Cannot convert to numeric: {str(e)}",
                success=False,
                error_message=f"Invalid numeric format: {value}"
            )
            return CleanResult(original_value, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.decimal_places is not None and not isinstance(self.decimal_places, int):
            errors.append("decimal_places must be integer or None")
        if not isinstance(self.remove_thousands_separators, bool):
            errors.append("remove_thousands_separators must be boolean")
        if not isinstance(self.scientific_notation, bool):
            errors.append("scientific_notation must be boolean")
        if not isinstance(self.allow_negative, bool):
            errors.append("allow_negative must be boolean")
        if self.min_value is not None and not isinstance(self.min_value, (int, float)):
            errors.append("min_value must be numeric or None")
        if self.max_value is not None and not isinstance(self.max_value, (int, float)):
            errors.append("max_value must be numeric or None")
        if self.min_value is not None and self.max_value is not None and self.min_value >= self.max_value:
            errors.append("min_value must be less than max_value")
        return errors


class StringCleaner(BaseCleaner):
    """Cleaner for standardizing string values."""
    
    def __init__(self, max_length: Optional[int] = None,
                 min_length: Optional[int] = None,
                 trim_whitespace: bool = True,
                 remove_control_chars: bool = True,
                 allowed_chars: Optional[str] = None,
                 forbidden_chars: Optional[str] = None,
                 required_chars: Optional[str] = None):
        super().__init__("string_cleaner", "1.0.0")
        self.max_length = max_length
        self.min_length = min_length
        self.trim_whitespace = trim_whitespace
        self.remove_control_chars = remove_control_chars
        self.allowed_chars = allowed_chars
        self.forbidden_chars = forbidden_chars
        self.required_chars = required_chars
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize string values."""
        if not isinstance(data, str):
            return CleanResult(data, [], context)
        
        original_data = data
        operations = []
        
        try:
            # Trim whitespace
            if self.trim_whitespace:
                old_data = data
                data = data.strip()
                operations.append(CleaningOperation(
                    field="string",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Trim whitespace",
                    before_value=old_data,
                    after_value=data
                ))
            
            # Remove control characters
            if self.remove_control_chars:
                old_data = data
                data = ''.join(c for c in data if ord(c) >= 32 or c in '\t\n\r')
                operations.append(CleaningOperation(
                    field="string",
                    operation_type=CleaningOperationType.REMOVE,
                    description="Remove control characters",
                    before_value=old_data,
                    after_value=data
                ))
            
            # Check length constraints
            if self.max_length is not None and len(data) > self.max_length:
                old_data = data
                data = data[:self.max_length]
                operations.append(CleaningOperation(
                    field="string",
                    operation_type=CleaningOperationType.TRUNCATE,
                    description=f"Truncate to {self.max_length} characters",
                    before_value=old_data,
                    after_value=data
                ))
            
            if self.min_length is not None and len(data) < self.min_length:
                operations.append(CleaningOperation(
                    field="string",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"String too short: {len(data)} < {self.min_length}",
                    success=False,
                    error_message=f"String too short: {len(data)} < {self.min_length}"
                ))
                return CleanResult(original_data, operations, context)
            
            # Check character constraints
            if self.allowed_chars is not None:
                old_data = data
                data = ''.join(c for c in data if c in self.allowed_chars)
                if data != old_data:
                    operations.append(CleaningOperation(
                        field="string",
                        operation_type=CleaningOperationType.REMOVE,
                        description=f"Keep only allowed characters: {self.allowed_chars}",
                        before_value=old_data,
                        after_value=data
                    ))
            
            if self.forbidden_chars is not None:
                old_data = data
                data = ''.join(c for c in data if c not in self.forbidden_chars)
                if data != old_data:
                    operations.append(CleaningOperation(
                        field="string",
                        operation_type=CleaningOperationType.REMOVE,
                        description=f"Remove forbidden characters: {self.forbidden_chars}",
                        before_value=old_data,
                        after_value=data
                    ))
            
            if self.required_chars is not None:
                missing_chars = [c for c in self.required_chars if c not in data]
                if missing_chars:
                    operations.append(CleaningOperation(
                        field="string",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Missing required characters: {missing_chars}",
                        success=False,
                        error_message=f"Missing required characters: {missing_chars}"
                    ))
                    return CleanResult(original_data, operations, context)
            
            return CleanResult(data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="string",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"String cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.max_length is not None and not isinstance(self.max_length, int):
            errors.append("max_length must be integer or None")
        if self.min_length is not None and not isinstance(self.min_length, int):
            errors.append("min_length must be integer or None")
        if self.min_length is not None and self.max_length is not None and self.min_length > self.max_length:
            errors.append("min_length must be less than or equal to max_length")
        if not isinstance(self.trim_whitespace, bool):
            errors.append("trim_whitespace must be boolean")
        if not isinstance(self.remove_control_chars, bool):
            errors.append("remove_control_chars must be boolean")
        if self.allowed_chars is not None and not isinstance(self.allowed_chars, str):
            errors.append("allowed_chars must be string or None")
        if self.forbidden_chars is not None and not isinstance(self.forbidden_chars, str):
            errors.append("forbidden_chars must be string or None")
        if self.required_chars is not None and not isinstance(self.required_chars, str):
            errors.append("required_chars must be string or None")
        return errors


class DateTimeCleaner(BaseCleaner):
    """Cleaner for standardizing date/time values."""
    
    def __init__(self, target_format: str = "ISO_8601",
                 input_formats: Optional[List[str]] = None,
                 timezone: Optional[str] = None,
                 allow_future: bool = True,
                 allow_past: bool = True,
                 min_date: Optional[str] = None,
                 max_date: Optional[str] = None):
        super().__init__("datetime_cleaner", "1.0.0")
        self.target_format = target_format
        self.input_formats = input_formats or ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]
        self.timezone = timezone
        self.allow_future = allow_future
        self.allow_past = allow_past
        self.min_date = min_date
        self.max_date = max_date
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize date/time values."""
        if isinstance(data, datetime):
            return self._clean_datetime(data, context)
        
        if isinstance(data, str):
            return self._clean_datetime_string(data, context)
        
        # Non-datetime data, return as-is
        return CleanResult(data, [], context)
    
    def _clean_datetime(self, dt: datetime, context: CleaningContext) -> CleanResult:
        """Clean datetime objects."""
        original_dt = dt
        operations = []
        
        try:
            # Apply timezone
            if self.timezone:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo(self.timezone)
                dt = dt.astimezone(tz)
                operations.append(CleaningOperation(
                    field="datetime",
                    operation_type=CleaningOperationType.TRANSFORM,
                    description=f"Convert to timezone {self.timezone}",
                    before_value=original_dt,
                    after_value=dt
                ))
            
            # Check date bounds
            if self.min_date:
                min_dt = datetime.fromisoformat(self.min_date)
                if dt < min_dt:
                    operations.append(CleaningOperation(
                        field="datetime",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Date {dt} before minimum {min_dt}",
                        success=False,
                        error_message=f"Date before minimum: {dt} < {min_dt}"
                    ))
                    return CleanResult(original_dt, operations, context)
            
            if self.max_date:
                max_dt = datetime.fromisoformat(self.max_date)
                if dt > max_dt:
                    operations.append(CleaningOperation(
                        field="datetime",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Date {dt} after maximum {max_dt}",
                        success=False,
                        error_message=f"Date after maximum: {dt} > {max_dt}"
                    ))
                    return CleanResult(original_dt, operations, context)
            
            # Format to target format
            if self.target_format == "ISO_8601":
                formatted = dt.isoformat()
            elif self.target_format == "timestamp":
                formatted = str(dt.timestamp())
            else:
                formatted = dt.strftime(self.target_format)
            
            operations.append(CleaningOperation(
                field="datetime",
                operation_type=CleaningOperationType.NORMALIZE,
                description=f"Format to {self.target_format}",
                before_value=original_dt,
                after_value=formatted
            ))
            
            return CleanResult(formatted, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="datetime",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Datetime cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_dt, [error_op], context)
    
    def _clean_datetime_string(self, value: str, context: CleaningContext) -> CleanResult:
        """Clean datetime strings."""
        original_value = value
        operations = []
        
        try:
            # Try different input formats
            dt = None
            for fmt in self.input_formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    operations.append(CleaningOperation(
                        field="datetime_string",
                        operation_type=CleaningOperationType.NORMALIZE,
                        description=f"Parsed with format {fmt}",
                        before_value=original_value,
                        after_value=dt
                    ))
                    break
                except ValueError:
                    continue
            
            if dt is None:
                # Use DataNormalizer for complex date parsing
                normalized_date, meta = DataNormalizer.normalize_date(value)
                dt = datetime.fromisoformat(normalized_date)
                operations.append(CleaningOperation(
                    field="datetime_string",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description=f"Normalized using DataNormalizer: {meta}",
                    before_value=original_value,
                    after_value=dt
                ))
            
            # Apply timezone
            if self.timezone:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo(self.timezone)
                dt = dt.astimezone(tz)
                operations.append(CleaningOperation(
                    field="datetime_string",
                    operation_type=CleaningOperationType.TRANSFORM,
                    description=f"Convert to timezone {self.timezone}",
                    before_value=dt,
                    after_value=dt
                ))
            
            # Check date bounds
            if self.min_date:
                min_dt = datetime.fromisoformat(self.min_date)
                if dt < min_dt:
                    operations.append(CleaningOperation(
                        field="datetime_string",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Date {dt} before minimum {min_dt}",
                        success=False,
                        error_message=f"Date before minimum: {dt} < {min_dt}"
                    ))
                    return CleanResult(original_value, operations, context)
            
            if self.max_date:
                max_dt = datetime.fromisoformat(self.max_date)
                if dt > max_dt:
                    operations.append(CleaningOperation(
                        field="datetime_string",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Date {dt} after maximum {max_dt}",
                        success=False,
                        error_message=f"Date after maximum: {dt} > {max_dt}"
                    ))
                    return CleanResult(original_value, operations, context)
            
            # Format to target format
            if self.target_format == "ISO_8601":
                formatted = dt.isoformat()
            elif self.target_format == "timestamp":
                formatted = str(dt.timestamp())
            else:
                formatted = dt.strftime(self.target_format)
            
            operations.append(CleaningOperation(
                field="datetime_string",
                operation_type=CleaningOperationType.NORMALIZE,
                description=f"Format to {self.target_format}",
                before_value=dt,
                after_value=formatted
            ))
            
            return CleanResult(formatted, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="datetime_string",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Datetime string cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_value, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.target_format not in ["ISO_8601", "timestamp"] and not isinstance(self.target_format, str):
            errors.append("target_format must be 'ISO_8601', 'timestamp', or a valid strftime format")
        if self.input_formats is not None and not isinstance(self.input_formats, list):
            errors.append("input_formats must be list or None")
        if self.timezone is not None and not isinstance(self.timezone, str):
            errors.append("timezone must be string or None")
        if not isinstance(self.allow_future, bool):
            errors.append("allow_future must be boolean")
        if not isinstance(self.allow_past, bool):
            errors.append("allow_past must be boolean")
        if self.min_date is not None and not isinstance(self.min_date, str):
            errors.append("min_date must be string or None")
        if self.max_date is not None and not isinstance(self.max_date, str):
            errors.append("max_date must be string or None")
        return errors