"""
Invoice data extractor.

This module implements extraction of invoice-specific information including
vendor details, dates, amounts, and tax information.
"""

import re
from typing import Any, Dict, Set, Tuple
from datetime import datetime
from decimal import Decimal

from ..core.base import BaseExtractor, EntityType


class InvoiceExtractor(BaseExtractor):
    """Extractor for invoice data."""
    
    def __init__(self, config: Dict[str, Any] = None) -> None:
        super().__init__(config)
        
        # Compile regex patterns for performance
        self._invoice_number_pattern = re.compile(
            r'(?:invoice|inv)[#\s]*([A-Z0-9\-]+)', 
            re.IGNORECASE
        )
        
        self._vendor_pattern = re.compile(
            r'(?:vendor|from|company):\s*([^|,\n]+)', 
            re.IGNORECASE
        )
        
        self._date_pattern = re.compile(
            r'(?:date|dated?):\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})', 
            re.IGNORECASE
        )
        
        self._amount_pattern = re.compile(
            r'(?:total|amount|sum):\s*([£$€¥₹]?[\d,]+\.?\d*)', 
            re.IGNORECASE
        )
        
        self._tax_pattern = re.compile(
            r'(?:vat|tax)\s*(\d+(?:\.\d+)?)\s*%', 
            re.IGNORECASE
        )
        
        # Currency symbols mapping
        self._currency_symbols = {
            '£': 'GBP',
            '$': 'USD', 
            '€': 'EUR',
            '¥': 'JPY',
            '₹': 'INR'
        }
    
    @property
    def supported_entity_types(self) -> Set[EntityType]:
        return {EntityType.INVOICE}
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract invoice data from text.
        
        Args:
            text: Input text to extract invoice data from.
            
        Returns:
            Tuple of (extracted_data, confidence_score)
        """
        extracted = {}
        confidence_factors = []
        
        # Extract invoice number
        invoice_match = self._invoice_number_pattern.search(text)
        if invoice_match:
            extracted['invoice_number'] = invoice_match.group(1).strip()
            confidence_factors.append(0.3)  # Strong indicator of invoice
        
        # Extract vendor information
        vendor_match = self._vendor_pattern.search(text)
        if vendor_match:
            extracted['vendor_name'] = vendor_match.group(1).strip()
            confidence_factors.append(0.2)
        
        # Extract date
        date_match = self._date_pattern.search(text)
        if date_match:
            extracted['invoice_date'] = date_match.group(1).strip()
            confidence_factors.append(0.15)
        
        # Extract amount and currency
        amount_match = self._amount_pattern.search(text)
        if amount_match:
            amount_str = amount_match.group(1)
            
            # Extract currency symbol if present
            currency_symbol = None
            for symbol in self._currency_symbols:
                if symbol in amount_str:
                    currency_symbol = symbol
                    amount_str = amount_str.replace(symbol, '').strip()
                    break
            
            # Clean amount string
            amount_str = amount_str.replace(',', '')
            
            try:
                amount_value = float(amount_str)
                extracted['total_amount'] = amount_value
                confidence_factors.append(0.25)
                
                if currency_symbol:
                    extracted['currency_code'] = self._currency_symbols[currency_symbol]
                    confidence_factors.append(0.1)
                    
            except ValueError:
                # Invalid amount format
                pass
        
        # Extract tax rate
        tax_match = self._tax_pattern.search(text)
        if tax_match:
            try:
                tax_rate = float(tax_match.group(1))
                extracted['tax_rate_percent'] = tax_rate
                confidence_factors.append(0.15)
            except ValueError:
                pass
        
        # Calculate overall confidence
        if confidence_factors:
            base_confidence = sum(confidence_factors)
            # Bonus for having multiple key fields
            field_bonus = min(0.2, len(extracted) * 0.05)
            final_confidence = min(1.0, base_confidence + field_bonus)
        else:
            final_confidence = 0.0
        
        return extracted, final_confidence
    
    def get_name(self) -> str:
        return "invoice_extractor"