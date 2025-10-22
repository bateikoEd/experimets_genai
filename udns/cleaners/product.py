"""
Product-specific cleaners for UDNS data cleaning.
"""

import re
from typing import Any, List, Optional, Dict, Union
from .base import BaseCleaner, CleaningContext, CleanResult, CleaningOperation, CleaningOperationType
from ..normalizers import DataNormalizer


class ProductNameCleaner(BaseCleaner):
    """Cleaner for standardizing product names."""
    
    def __init__(self, remove_brand_prefixes: bool = True,
                 remove_suffixes: bool = True,
                 standardize_case: bool = True,
                 target_case: str = "title",
                 brand_prefixes: Optional[List[str]] = None,
                 product_suffixes: Optional[List[str]] = None):
        super().__init__("product_name_cleaner", "1.0.0")
        self.remove_brand_prefixes = remove_brand_prefixes
        self.remove_suffixes = remove_suffixes
        self.standardize_case = standardize_case
        self.target_case = target_case
        self.brand_prefixes = brand_prefixes or ["Apple", "Samsung", "Sony", "LG", "Microsoft", "Google", "Amazon", "HP", "Dell", "Lenovo"]
        self.product_suffixes = product_suffixes or ["Inc", "Ltd", "Corp", "LLC", "GmbH", "S.A.", "Pty Ltd", "Co.", "Company"]
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize product names."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Remove brand prefixes
            if self.remove_brand_prefixes:
                for prefix in self.brand_prefixes:
                    if data.startswith(prefix + " "):
                        old_data = data
                        data = data[len(prefix) + 1:].strip()
                        operations.append(CleaningOperation(
                            field="product_name",
                            operation_type=CleaningOperationType.REMOVE,
                            description=f"Remove brand prefix '{prefix}'",
                            before_value=old_data,
                            after_value=data
                        ))
                        break
            
            # Remove product suffixes
            if self.remove_suffixes:
                for suffix in self.product_suffixes:
                    if data.endswith(" " + suffix) or data.endswith(" " + suffix + "."):
                        old_data = data
                        data = data[:-len(suffix)].strip()
                        operations.append(CleaningOperation(
                            field="product_name",
                            operation_type=CleaningOperationType.REMOVE,
                            description=f"Remove product suffix '{suffix}'",
                            before_value=old_data,
                            after_value=data
                        ))
                        break
            
            # Remove extra spaces
            old_data = data
            data = re.sub(r'\s+', ' ', data).strip()
            operations.append(CleaningOperation(
                field="product_name",
                operation_type=CleaningOperationType.NORMALIZE,
                description="Remove extra spaces",
                before_value=old_data,
                after_value=data
            ))
            
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
                    field="product_name",
                    operation_type=CleaningOperationType.STANDARDIZE,
                    description=f"Convert to {self.target_case} case",
                    before_value=old_data,
                    after_value=data
                ))
            
            return CleanResult(data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="product_name",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Product name cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if not isinstance(self.remove_brand_prefixes, bool):
            errors.append("remove_brand_prefixes must be boolean")
        if not isinstance(self.remove_suffixes, bool):
            errors.append("remove_suffixes must be boolean")
        if not isinstance(self.standardize_case, bool):
            errors.append("standardize_case must be boolean")
        if self.target_case not in ["title", "upper", "lower"]:
            errors.append("target_case must be 'title', 'upper', or 'lower'")
        if self.brand_prefixes is not None and not isinstance(self.brand_prefixes, list):
            errors.append("brand_prefixes must be list or None")
        if self.product_suffixes is not None and not isinstance(self.product_suffixes, list):
            errors.append("product_suffixes must be list or None")
        return errors


class ProductPriceCleaner(BaseCleaner):
    """Cleaner for standardizing product prices."""
    
    def __init__(self, remove_currency_symbols: bool = True,
                 standardize_decimals: bool = True,
                 min_price: Optional[float] = None,
                 max_price: Optional[float] = None,
                 currency_hint: Optional[str] = None):
        super().__init__("product_price_cleaner", "1.0.0")
        self.remove_currency_symbols = remove_currency_symbols
        self.standardize_decimals = standardize_decimals
        self.min_price = min_price
        self.max_price = max_price
        self.currency_hint = currency_hint
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize product prices."""
        if isinstance(data, (int, float)):
            return self._clean_numeric_price(data, context)
        
        if isinstance(data, str):
            return self._clean_string_price(data, context)
        
        # Non-price data, return as-is
        return CleanResult(data, [], context)
    
    def _clean_numeric_price(self, price: Union[int, float], context: CleaningContext) -> CleanResult:
        """Clean numeric prices."""
        original_price = price
        operations = []
        
        try:
            # Check bounds
            if self.min_price is not None and price < self.min_price:
                operations.append(CleaningOperation(
                    field="product_price",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Price {price} below minimum {self.min_price}",
                    success=False,
                    error_message=f"Price below minimum: {price} < {self.min_price}"
                ))
                return CleanResult(original_price, operations, context)
            
            if self.max_price is not None and price > self.max_price:
                operations.append(CleaningOperation(
                    field="product_price",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Price {price} above maximum {self.max_price}",
                    success=False,
                    error_message=f"Price above maximum: {price} > {self.max_price}"
                ))
                return CleanResult(original_price, operations, context)
            
            # Standardize decimals
            if self.standardize_decimals:
                old_price = price
                price = round(float(price), 2)
                operations.append(CleaningOperation(
                    field="product_price",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Round to 2 decimal places",
                    before_value=old_price,
                    after_value=price
                ))
            
            return CleanResult(price, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="product_price",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Product price cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_price, [error_op], context)
    
    def _clean_string_price(self, price_str: str, context: CleaningContext) -> CleanResult:
        """Clean string prices."""
        original_price = price_str
        operations = []
        
        try:
            # Use DataNormalizer for currency parsing
            currency_data, meta = DataNormalizer.normalize_currency(price_str, self.currency_hint)
            price = currency_data['amount']
            
            operations.append(CleaningOperation(
                field="product_price",
                operation_type=CleaningOperationType.NORMALIZE,
                description=f"Parse currency: {meta}",
                before_value=original_price,
                after_value=price
            ))
            
            # Check bounds
            if self.min_price is not None and price < self.min_price:
                operations.append(CleaningOperation(
                    field="product_price",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Price {price} below minimum {self.min_price}",
                    success=False,
                    error_message=f"Price below minimum: {price} < {self.min_price}"
                ))
                return CleanResult(original_price, operations, context)
            
            if self.max_price is not None and price > self.max_price:
                operations.append(CleaningOperation(
                    field="product_price",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Price {price} above maximum {self.max_price}",
                    success=False,
                    error_message=f"Price above maximum: {price} > {self.max_price}"
                ))
                return CleanResult(original_price, operations, context)
            
            # Standardize decimals
            if self.standardize_decimals:
                old_price = price
                price = round(price, 2)
                operations.append(CleaningOperation(
                    field="product_price",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Round to 2 decimal places",
                    before_value=old_price,
                    after_value=price
                ))
            
            return CleanResult(price, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="product_price",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Product price cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_price, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if not isinstance(self.remove_currency_symbols, bool):
            errors.append("remove_currency_symbols must be boolean")
        if not isinstance(self.standardize_decimals, bool):
            errors.append("standardize_decimals must be boolean")
        if self.min_price is not None and not isinstance(self.min_price, (int, float)):
            errors.append("min_price must be numeric or None")
        if self.max_price is not None and not isinstance(self.max_price, (int, float)):
            errors.append("max_price must be numeric or None")
        if self.min_price is not None and self.max_price is not None and self.min_price >= self.max_price:
            errors.append("min_price must be less than max_price")
        if self.currency_hint is not None and not isinstance(self.currency_hint, str):
            errors.append("currency_hint must be string or None")
        return errors


class ProductWeightCleaner(BaseCleaner):
    """Cleaner for standardizing product weights."""
    
    def __init__(self, target_unit: str = "kg",
                 standardize_decimals: bool = True,
                 min_weight: Optional[float] = None,
                 max_weight: Optional[float] = None):
        super().__init__("product_weight_cleaner", "1.0.0")
        self.target_unit = target_unit
        self.standardize_decimals = standardize_decimals
        self.min_weight = min_weight
        self.max_weight = max_weight
        
        # Unit conversion factors
        self.unit_conversions = {
            "kg": 1.0,
            "g": 0.001,
            "lb": 0.453592,
            "oz": 0.0283495,
            "ton": 1000.0,
            "tonne": 1000.0
        }
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize product weights."""
        if isinstance(data, (int, float)):
            return self._clean_numeric_weight(data, context)
        
        if isinstance(data, str):
            return self._clean_string_weight(data, context)
        
        # Non-weight data, return as-is
        return CleanResult(data, [], context)
    
    def _clean_numeric_weight(self, weight: Union[int, float], context: CleaningContext) -> CleanResult:
        """Clean numeric weights."""
        original_weight = weight
        operations = []
        
        try:
            # Assume weight is in target unit
            weight_kg = weight
            
            # Check bounds
            if self.min_weight is not None and weight_kg < self.min_weight:
                operations.append(CleaningOperation(
                    field="product_weight",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Weight {weight_kg} below minimum {self.min_weight}",
                    success=False,
                    error_message=f"Weight below minimum: {weight_kg} < {self.min_weight}"
                ))
                return CleanResult(original_weight, operations, context)
            
            if self.max_weight is not None and weight_kg > self.max_weight:
                operations.append(CleaningOperation(
                    field="product_weight",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Weight {weight_kg} above maximum {self.max_weight}",
                    success=False,
                    error_message=f"Weight above maximum: {weight_kg} > {self.max_weight}"
                ))
                return CleanResult(original_weight, operations, context)
            
            # Standardize decimals
            if self.standardize_decimals:
                old_weight = weight_kg
                weight_kg = round(weight_kg, 3)
                operations.append(CleaningOperation(
                    field="product_weight",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Round to 3 decimal places",
                    before_value=old_weight,
                    after_value=weight_kg
                ))
            
            return CleanResult(weight_kg, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="product_weight",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Product weight cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_weight, [error_op], context)
    
    def _clean_string_weight(self, weight_str: str, context: CleaningContext) -> CleanResult:
        """Clean string weights."""
        original_weight = weight_str
        operations = []
        
        try:
            # Parse weight with unit
            weight_pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)'
            match = re.search(weight_pattern, weight_str)
            
            if not match:
                # Try to extract just the number
                number_match = re.search(r'(\d+(?:\.\d+)?)', weight_str)
                if number_match:
                    weight_kg = float(number_match.group(1))
                    operations.append(CleaningOperation(
                        field="product_weight",
                        operation_type=CleaningOperationType.NORMALIZE,
                        description="Extract numeric weight",
                        before_value=original_weight,
                        after_value=weight_kg
                    ))
                else:
                    raise ValueError(f"Could not parse weight: {weight_str}")
            else:
                weight_value = float(match.group(1))
                unit = match.group(2).lower()
                
                # Convert to kg
                if unit in self.unit_conversions:
                    weight_kg = weight_value * self.unit_conversions[unit]
                    operations.append(CleaningOperation(
                        field="product_weight",
                        operation_type=CleaningOperationType.CONVERT,
                        description=f"Convert {weight_value}{unit} to {weight_kg}kg",
                        before_value=weight_value,
                        after_value=weight_kg
                    ))
                else:
                    # Assume kg if unit not recognized
                    weight_kg = weight_value
                    operations.append(CleaningOperation(
                        field="product_weight",
                        operation_type=CleaningOperationType.NORMALIZE,
                        description=f"Assume kg for unknown unit: {unit}",
                        before_value=weight_value,
                        after_value=weight_kg
                    ))
            
            # Check bounds
            if self.min_weight is not None and weight_kg < self.min_weight:
                operations.append(CleaningOperation(
                    field="product_weight",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Weight {weight_kg} below minimum {self.min_weight}",
                    success=False,
                    error_message=f"Weight below minimum: {weight_kg} < {self.min_weight}"
                ))
                return CleanResult(original_weight, operations, context)
            
            if self.max_weight is not None and weight_kg > self.max_weight:
                operations.append(CleaningOperation(
                    field="product_weight",
                    operation_type=CleaningOperationType.VALIDATE,
                    description=f"Weight {weight_kg} above maximum {self.max_weight}",
                    success=False,
                    error_message=f"Weight above maximum: {weight_kg} > {self.max_weight}"
                ))
                return CleanResult(original_weight, operations, context)
            
            # Standardize decimals
            if self.standardize_decimals:
                old_weight = weight_kg
                weight_kg = round(weight_kg, 3)
                operations.append(CleaningOperation(
                    field="product_weight",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Round to 3 decimal places",
                    before_value=old_weight,
                    after_value=weight_kg
                ))
            
            return CleanResult(weight_kg, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="product_weight",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Product weight cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_weight, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.target_unit not in self.unit_conversions:
            errors.append(f"target_unit must be one of: {list(self.unit_conversions.keys())}")
        if not isinstance(self.standardize_decimals, bool):
            errors.append("standardize_decimals must be boolean")
        if self.min_weight is not None and not isinstance(self.min_weight, (int, float)):
            errors.append("min_weight must be numeric or None")
        if self.max_weight is not None and not isinstance(self.max_weight, (int, float)):
            errors.append("max_weight must be numeric or None")
        if self.min_weight is not None and self.max_weight is not None and self.min_weight >= self.max_weight:
            errors.append("min_weight must be less than max_weight")
        return errors


class ProductCategoryCleaner(BaseCleaner):
    """Cleaner for standardizing product categories."""
    
    def __init__(self, standardize_hierarchy: bool = True,
                 remove_duplicates: bool = True,
                 target_separator: str = ">",
                 category_mappings: Optional[Dict[str, str]] = None):
        super().__init__("product_category_cleaner", "1.0.0")
        self.standardize_hierarchy = standardize_hierarchy
        self.remove_duplicates = remove_duplicates
        self.target_separator = target_separator
        self.category_mappings = category_mappings or {
            "electronics": "Electronics",
            "tech": "Technology",
            "comp": "Computers",
            "phone": "Mobile Phones",
            "smartphone": "Mobile Phones",
            "laptop": "Laptops",
            "desktop": "Desktops",
            "tablet": "Tablets",
            "wearable": "Wearables",
            "audio": "Audio",
            "headphones": "Headphones",
            "speakers": "Speakers",
            "home": "Home",
            "household": "Home",
            "kitchen": "Kitchen",
            "appliances": "Appliances",
            "clothing": "Clothing",
            "fashion": "Fashion",
            "shoes": "Footwear",
            "accessories": "Accessories",
            "beauty": "Beauty",
            "health": "Health",
            "fitness": "Fitness",
            "sports": "Sports",
            "outdoors": "Outdoor",
            "books": "Books",
            "media": "Media",
            "music": "Music",
            "movies": "Movies",
            "games": "Games",
            "toys": "Toys",
            "baby": "Baby",
            "kids": "Kids",
            "pets": "Pets",
            "automotive": "Automotive",
            "tools": "Tools",
            "hardware": "Hardware",
            "garden": "Garden",
            "food": "Food",
            "grocery": "Grocery",
            "beverages": "Beverages",
            "wine": "Alcohol",
            "beer": "Alcohol",
            "spirits": "Alcohol"
        }
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize product categories."""
        if isinstance(data, str):
            return self._clean_string_category(data, context)
        elif isinstance(data, list):
            return self._clean_list_category(data, context)
        
        # Non-category data, return as-is
        return CleanResult(data, [], context)
    
    def _clean_string_category(self, category_str: str, context: CleaningContext) -> CleanResult:
        """Clean string categories."""
        original_data = category_str
        operations = []
        
        try:
            # Split by common separators
            separators = [">", "/", ">", "|", ",", "-"]
            categories = []
            
            for sep in separators:
                if sep in category_str:
                    categories = [cat.strip() for cat in category_str.split(sep) if cat.strip()]
                    operations.append(CleaningOperation(
                        field="product_category",
                        operation_type=CleaningOperationType.SPLIT,
                        description=f"Split by separator '{sep}'",
                        before_value=category_str,
                        after_value=categories
                    ))
                    break
            
            if not categories:
                categories = [category_str.strip()]
            
            # Standardize each category
            standardized_categories = []
            for category in categories:
                standardized = self._standardize_category(category)
                standardized_categories.append(standardized)
            
            # Remove duplicates
            if self.remove_duplicates:
                old_categories = standardized_categories
                standardized_categories = list(dict.fromkeys(standardized_categories))
                
                if len(standardized_categories) < len(old_categories):
                    operations.append(CleaningOperation(
                        field="product_category",
                        operation_type=CleaningOperationType.REMOVE,
                        description="Remove duplicate categories",
                        before_value=old_categories,
                        after_value=standardized_categories
                    ))
            
            # Format to target separator
            if self.standardize_hierarchy:
                old_categories = standardized_categories
                category_str = self.target_separator.join(standardized_categories)
                
                operations.append(CleaningOperation(
                    field="product_category",
                    operation_type=CleaningOperationType.FORMAT,
                    description=f"Format with '{self.target_separator}' separator",
                    before_value=old_categories,
                    after_value=category_str
                ))
            
            return CleanResult(category_str, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="product_category",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Product category cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def _clean_list_category(self, categories: List[str], context: CleaningContext) -> CleanResult:
        """Clean list categories."""
        original_data = categories
        operations = []
        
        try:
            # Standardize each category
            standardized_categories = []
            for category in categories:
                standardized = self._standardize_category(category)
                standardized_categories.append(standardized)
            
            # Remove duplicates
            if self.remove_duplicates:
                old_categories = standardized_categories
                standardized_categories = list(dict.fromkeys(standardized_categories))
                
                if len(standardized_categories) < len(old_categories):
                    operations.append(CleaningOperation(
                        field="product_category",
                        operation_type=CleaningOperationType.REMOVE,
                        description="Remove duplicate categories",
                        before_value=old_categories,
                        after_value=standardized_categories
                    ))
            
            # Format to target separator
            if self.standardize_hierarchy:
                old_categories = standardized_categories
                category_str = self.target_separator.join(standardized_categories)
                
                operations.append(CleaningOperation(
                    field="product_category",
                    operation_type=CleaningOperationType.FORMAT,
                    description=f"Format with '{self.target_separator}' separator",
                    before_value=old_categories,
                    after_value=category_str
                ))
                result = category_str
            else:
                result = standardized_categories
            
            return CleanResult(result, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="product_category",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Product category cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def _standardize_category(self, category: str) -> str:
        """Standardize a single category."""
        category = category.strip().lower()
        
        # Apply mappings
        if category in self.category_mappings:
            return self.category_mappings[category]
        
        # Title case for unmapped categories
        return category.title()
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if not isinstance(self.standardize_hierarchy, bool):
            errors.append("standardize_hierarchy must be boolean")
        if not isinstance(self.remove_duplicates, bool):
            errors.append("remove_duplicates must be boolean")
        if not isinstance(self.target_separator, str):
            errors.append("target_separator must be string")
        if self.category_mappings is not None and not isinstance(self.category_mappings, dict):
            errors.append("category_mappings must be dict or None")
        return errors