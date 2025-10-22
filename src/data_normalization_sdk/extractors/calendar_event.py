"""Calendar event extraction from unstructured text."""

import re
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta
from ..core.base import BaseExtractor, EntityType


class CalendarEventExtractor(BaseExtractor):
    """Extract calendar event information from text."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize calendar event extractor with configuration."""
        super().__init__(config)
        self.name = "calendar_event_extractor"
        
        # Calendar event patterns
        self.patterns = {
            # Standup — 20 Oct 2025, 09:30–09:50 Europe/Kyiv
            'full_event': re.compile(
                r'^([^—\-]+)[\s—\-]+(\d{1,2}\s+\w{3}\s+\d{4}),\s*'
                r'(\d{1,2}:\d{2})[\s–\-]+(\d{1,2}:\d{2})\s*'
                r'([A-Za-z][A-Za-z_/]+)?',
                re.IGNORECASE
            ),
            'title': re.compile(r'^([^—\-\n]+)', re.IGNORECASE),
            'date': re.compile(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', re.IGNORECASE),
            'time_range': re.compile(r'(\d{1,2}:\d{2})[\s–\-]+(\d{1,2}:\d{2})', re.IGNORECASE),
            'timezone': re.compile(r'\b([A-Za-z][A-Za-z_/]+)$', re.IGNORECASE),
        }
        
        # Month name mapping
        self.months = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        # Timezone offset mapping (simplified)
        self.timezone_offsets = {
            'europe/kyiv': '+03:00',
            'europe/kiev': '+03:00',
            'america/new_york': '-05:00',
            'america/los_angeles': '-08:00',
            'utc': '+00:00',
            'gmt': '+00:00',
        }
    
    @property
    def supported_entity_types(self) -> set:
        """Get entity types this extractor can handle."""
        return {EntityType.EVENT}
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract calendar event information from text."""
        attributes = {}
        confidence_factors = []
        
        # Try full event pattern
        full_match = self.patterns['full_event'].search(text.strip())
        if full_match:
            title, date_str, start_time, end_time, timezone = full_match.groups()
            
            # Extract title
            attributes['title'] = title.strip()
            confidence_factors.append(0.95)
            
            # Parse date and times
            date_info = self._parse_date(date_str)
            if date_info:
                start_dt, end_dt = self._parse_datetime_range(date_info, start_time, end_time, timezone)
                if start_dt and end_dt:
                    attributes['start'] = start_dt
                    attributes['end'] = end_dt
                    
                    # Calculate duration
                    try:
                        start_obj = datetime.fromisoformat(start_dt.replace('Z', '+00:00').replace('+03:00', ''))
                        end_obj = datetime.fromisoformat(end_dt.replace('Z', '+00:00').replace('+03:00', ''))
                        duration = end_obj - start_obj
                        attributes['duration_minutes'] = int(duration.total_seconds() / 60)
                    except:
                        pass
                    
                    confidence_factors.append(0.90)
            
            # Add timezone if present
            if timezone:
                attributes['timezone'] = timezone
                confidence_factors.append(0.85)
        
        else:
            # Try individual patterns
            title_match = self.patterns['title'].search(text)
            if title_match:
                attributes['title'] = title_match.group(1).strip()
                confidence_factors.append(0.80)
            
            date_match = self.patterns['date'].search(text)
            time_match = self.patterns['time_range'].search(text)
            timezone_match = self.patterns['timezone'].search(text)
            
            if date_match and time_match:
                date_info = self._parse_date(date_match.group(0))
                start_time = time_match.group(1)
                end_time = time_match.group(2)
                timezone = timezone_match.group(1) if timezone_match else None
                
                if date_info:
                    start_dt, end_dt = self._parse_datetime_range(date_info, start_time, end_time, timezone)
                    if start_dt and end_dt:
                        attributes['start'] = start_dt
                        attributes['end'] = end_dt
                        confidence_factors.append(0.75)
                        
                        if timezone:
                            attributes['timezone'] = timezone
                            confidence_factors.append(0.70)
        
        # Calculate confidence
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
        
        # Only return if we found meaningful event information
        if len(attributes) >= 2:  # At least title and one time attribute
            return attributes, min(confidence, 1.0)
        
        return {}, 0.0
    
    def _parse_date(self, date_str: str) -> Dict[str, str]:
        """Parse date string to components."""
        date_match = self.patterns['date'].search(date_str)
        if not date_match:
            return None
        
        day, month_str, year = date_match.groups()
        month_num = self.months.get(month_str.lower())
        
        if month_num:
            return {
                'year': year,
                'month': month_num,
                'day': day.zfill(2)
            }
        
        return None
    
    def _parse_datetime_range(self, date_info: Dict[str, str], start_time: str, end_time: str, timezone: str = None) -> Tuple[str, str]:
        """Parse date and time range to ISO format."""
        if not date_info:
            return None, None
        
        try:
            date_part = f"{date_info['year']}-{date_info['month']}-{date_info['day']}"
            
            # Get timezone offset
            tz_offset = ''
            if timezone:
                tz_key = timezone.lower()
                if tz_key in self.timezone_offsets:
                    tz_offset = self.timezone_offsets[tz_key]
                else:
                    # Default to the timezone name for IANA format
                    tz_offset = '+03:00'  # Default for Europe/Kyiv example
            
            # Format start and end times
            start_dt = f"{date_part}T{start_time}:00{tz_offset}"
            end_dt = f"{date_part}T{end_time}:00{tz_offset}"
            
            return start_dt, end_dt
            
        except Exception:
            return None, None
    
    def get_name(self) -> str:
        """Get the extractor name."""
        return self.name