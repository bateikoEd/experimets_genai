"""
Address-specific cleaners for UDNS data cleaning.
"""

import re
from typing import Any, List, Optional, Dict
from .base import BaseCleaner, CleaningContext, CleanResult, CleaningOperation, CleaningOperationType
from ..normalizers import DataNormalizer


class AddressComponentCleaner(BaseCleaner):
    """Cleaner for standardizing address components."""
    
    def __init__(self, standardize_directionals: bool = True,
                 standardize_suffixes: bool = True,
                 remove_extra_spaces: bool = True,
                 directionals_map: Optional[Dict[str, str]] = None,
                 suffixes_map: Optional[Dict[str, str]] = None):
        super().__init__("address_component_cleaner", "1.0.0")
        self.standardize_directionals = standardize_directionals
        self.standardize_suffixes = standardize_suffixes
        self.remove_extra_spaces = remove_extra_spaces
        self.directionals_map = directionals_map or {
            "N": "North", "S": "South", "E": "East", "W": "West",
            "NE": "Northeast", "NW": "Northwest", "SE": "Southeast", "SW": "Southwest"
        }
        self.suffixes_map = suffixes_map or {
            "St": "Street", "Ave": "Avenue", "Blvd": "Boulevard", "Rd": "Road",
            "Ln": "Lane", "Dr": "Drive", "Ct": "Court", "Pl": "Place",
            "Ter": "Terrace", "Way": "Way", "Pkwy": "Parkway", "Hwy": "Highway"
        }
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize address components."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Standardize directionals
            if self.standardize_directionals:
                for short, long in self.directionals_map.items():
                    if data.startswith(short + " ") or data.startswith(short + "."):
                        old_data = data
                        data = long + data[len(short):].strip()
                        operations.append(CleaningOperation(
                            field="address_component",
                            operation_type=CleaningOperationType.STANDARDIZE,
                            description=f"Expand directional '{short}' to '{long}'",
                            before_value=old_data,
                            after_value=data
                        ))
                        break
            
            # Standardize suffixes
            if self.standardize_suffixes:
                for short, long in self.suffixes_map.items():
                    if data.endswith(" " + short) or data.endswith(" " + short + "."):
                        old_data = data
                        data = data[:-len(short)].strip() + " " + long
                        operations.append(CleaningOperation(
                            field="address_component",
                            operation_type=CleaningOperationType.STANDARDIZE,
                            description=f"Expand suffix '{short}' to '{long}'",
                            before_value=old_data,
                            after_value=data
                        ))
                        break
            
            # Remove extra spaces
            if self.remove_extra_spaces:
                old_data = data
                data = re.sub(r'\s+', ' ', data).strip()
                operations.append(CleaningOperation(
                    field="address_component",
                    operation_type=CleaningOperationType.NORMALIZE,
                    description="Remove extra spaces",
                    before_value=old_data,
                    after_value=data
                ))
            
            return CleanResult(data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="address_component",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Address component cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if not isinstance(self.standardize_directionals, bool):
            errors.append("standardize_directionals must be boolean")
        if not isinstance(self.standardize_suffixes, bool):
            errors.append("standardize_suffixes must be boolean")
        if not isinstance(self.remove_extra_spaces, bool):
            errors.append("remove_extra_spaces must be boolean")
        if self.directionals_map is not None and not isinstance(self.directionals_map, dict):
            errors.append("directionals_map must be dict or None")
        if self.suffixes_map is not None and not isinstance(self.suffixes_map, dict):
            errors.append("suffixes_map must be dict or None")
        return errors


class PostalCodeCleaner(BaseCleaner):
    """Cleaner for standardizing postal codes."""
    
    def __init__(self, target_format: str = "basic",
                 validate_format: bool = True,
                 country_hint: Optional[str] = None):
        super().__init__("postal_code_cleaner", "1.0.0")
        self.target_format = target_format
        self.validate_format = validate_format
        self.country_hint = country_hint
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize postal codes."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Remove spaces and hyphens
            old_data = data
            data = re.sub(r'[\s\-]', '', data).upper()
            operations.append(CleaningOperation(
                field="postal_code",
                operation_type=CleaningOperationType.NORMALIZE,
                description="Remove spaces and hyphens, convert to uppercase",
                before_value=old_data,
                after_value=data
            ))
            
            # Validate format if requested
            if self.validate_format:
                if not self._is_valid_postal_code(data):
                    operations.append(CleaningOperation(
                        field="postal_code",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Invalid postal code format: {data}",
                        success=False,
                        error_message=f"Invalid postal code format: {data}"
                    ))
                    return CleanResult(original_data, operations, context)
            
            # Apply target format
            if self.target_format == "with_spaces" and len(data) > 3:
                old_data = data
                if len(data) == 5:  # US ZIP
                    data = f"{data[:3]} {data[3:]}"
                elif len(data) == 6:  # Canadian postal code
                    data = f"{data[:3]} {data[3:]}"
                elif len(data) == 7:  # UK postcode
                    data = f"{data[:4]} {data[4:]}"
                
                if old_data != data:
                    operations.append(CleaningOperation(
                        field="postal_code",
                        operation_type=CleaningOperationType.FORMAT,
                        description=f"Format to {self.target_format}",
                        before_value=old_data,
                        after_value=data
                    ))
            
            return CleanResult(data, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="postal_code",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Postal code cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def _is_valid_postal_code(self, postal_code: str) -> bool:
        """Validate postal code format based on country hint."""
        if not postal_code:
            return False
        
        if self.country_hint:
            if self.country_hint.upper() == "US":
                return re.match(r'^\d{5}(-\d{4})?$', postal_code) is not None
            elif self.country_hint.upper() == "CA":
                return re.match(r'^[A-Z]\d[A-Z]\s?\d[A-Z]\d$', postal_code) is not None
            elif self.country_hint.upper() == "GB":
                return re.match(r'^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$', postal_code) is not None
            elif self.country_hint.upper() == "DE":
                return re.match(r'^\d{5}$', postal_code) is not None
            elif self.country_hint.upper() == "FR":
                return re.match(r'^\d{5}$', postal_code) is not None
            elif self.country_hint.upper() == "JP":
                return re.match(r'^\d{3}-\d{4}$', postal_code) is not None
        
        # Generic validation for unknown country
        return len(postal_code) >= 3 and len(postal_code) <= 10 and postal_code.isalnum()
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.target_format not in ["basic", "with_spaces"]:
            errors.append("target_format must be 'basic' or 'with_spaces'")
        if not isinstance(self.validate_format, bool):
            errors.append("validate_format must be boolean")
        if self.country_hint is not None and not isinstance(self.country_hint, str):
            errors.append("country_hint must be string or None")
        return errors


class CountryCleaner(BaseCleaner):
    """Cleaner for standardizing country names and codes."""
    
    def __init__(self, output_format: str = "name",
                 standardize_names: bool = True,
                 include_alternative_names: bool = False):
        super().__init__("country_cleaner", "1.0.0")
        self.output_format = output_format
        self.standardize_names = standardize_names
        self.include_alternative_names = include_alternative_names
        
        # Country name mappings
        self.country_mappings = {
            "USA": ["United States", "US", "America", "United States of America"],
            "GBR": ["United Kingdom", "UK", "Great Britain", "England", "Britain"],
            "UKR": ["Ukraine", "UA"],
            "DEU": ["Germany", "DE"],
            "FRA": ["France", "FR"],
            "JPN": ["Japan", "JP"],
            "CHN": ["China", "CN"],
            "CAN": ["Canada", "CA"],
            "AUS": ["Australia", "AU"],
            "BRA": ["Brazil", "BR"],
            "IND": ["India", "IN"],
            "RUS": ["Russia", "RU"],
            "ITA": ["Italy", "IT"],
            "ESP": ["Spain", "ES"],
            "MEX": ["Mexico", "MX"],
            "KOR": ["South Korea", "KR", "Korea"],
            "NLD": ["Netherlands", "NL", "Holland"],
            "SAU": ["Saudi Arabia", "SA"],
            "TUR": ["Turkey", "TR"],
            "SWE": ["Sweden", "SE"],
            "NOR": ["Norway", "NO"],
            "DNK": ["Denmark", "DK"],
            "FIN": ["Finland", "FI"],
            "POL": ["Poland", "PL"],
            "BEL": ["Belgium", "BE"],
            "AUT": ["Austria", "AT"],
            "CHE": ["Switzerland", "CH", "Swiss"],
            "IRL": ["Ireland", "IE"],
            "NZL": ["New Zealand", "NZ"],
            "ZAF": ["South Africa", "ZA"],
            "EGY": ["Egypt", "EG"],
            "ARG": ["Argentina", "AR"],
            "CHL": ["Chile", "CL"],
            "COL": ["Colombia", "CO"],
            "PER": ["Peru", "PE"],
            "VNM": ["Vietnam", "VN"],
            "THA": ["Thailand", "TH"],
            "SGP": ["Singapore", "SG"],
            "MYS": ["Malaysia", "MY"],
            "IDN": ["Indonesia", "ID"],
            "PHL": ["Philippines", "PH"],
            "PAK": ["Pakistan", "PK"],
            "BGD": ["Bangladesh", "BD"],
            "NGA": ["Nigeria", "NG"],
            "ETH": ["Ethiopia", "ET"],
            "EGY": ["Egypt", "EG"],
            "MAR": ["Morocco", "MA"],
            "TUN": ["Tunisia", "TN"],
            "ZAF": ["South Africa", "ZA"],
            "KEN": ["Kenya", "KE"],
            "GHA": ["Ghana", "GH"],
            "TZA": ["Tanzania", "TZ"],
            "UGA": ["Uganda", "UG"],
            "AGO": ["Angola", "AO"],
            "MOZ": ["Mozambique", "MZ"],
            "ZWE": ["Zimbabwe", "ZW"],
            "ZMB": ["Zambia", "ZM"],
            "MWI": ["Malawi", "MW"],
            "LSO": ["Lesotho", "LS"],
            "SWZ": ["Eswatini", "SZ"],
            "NAM": ["Namibia", "NA"],
            "BWA": ["Botswana", "BW"],
            "LBY": ["Libya", "LY"],
            "DZA": ["Algeria", "DZ"],
            "TCD": ["Chad", "TD"],
            "NER": ["Niger", "NE"],
            "MLI": ["Mali", "ML"],
            "SEN": ["Senegal", "SN"],
            "CIV": ["Ivory Coast", "CI", "Côte d'Ivoire"],
            "BFA": ["Burkina Faso", "BF"],
            "GIN": ["Guinea", "GN"],
            "GNB": ["Guinea-Bissau", "GW"],
            "SLE": ["Sierra Leone", "SL"],
            "LBR": ["Liberia", "LR"],
            "CIV": ["Ivory Coast", "CI"],
            "GHA": ["Ghana", "GH"],
            "TGO": ["Togo", "TG"],
            "BEN": ["Benin", "BJ"],
            "NER": ["Niger", "NE"],
            "CMR": ["Cameroon", "CM"],
            "CAF": ["Central African Republic", "CF"],
            "TCD": ["Chad", "TD"],
            "COG": ["Republic of the Congo", "CG"],
            "COD": ["Democratic Republic of the Congo", "CD"],
            "GNQ": ["Equatorial Guinea", "GQ"],
            "GAB": ["Gabon", "GA"],
            "STP": ["São Tomé and Príncipe", "ST"],
            "CPV": ["Cape Verde", "CV"],
            "BWA": ["Botswana", "BW"],
            "NAM": ["Namibia", "NA"],
            "ZAF": ["South Africa", "ZA"],
            "LSO": ["Lesotho", "LS"],
            "SWZ": ["Eswatini", "SZ"],
            "MDG": ["Madagascar", "MG"],
            "COM": ["Comoros", "KM"],
            "MYT": ["Mayotte", "YT"],
            "REU": ["Réunion", "RE"],
            "MUS": ["Mauritius", "MU"],
            "SYC": ["Seychelles", "SC"],
            "DJI": ["Djibouti", "DJ"],
            "ERI": ["Eritrea", "ER"],
            "SOM": ["Somalia", "SO"],
            "KEN": ["Kenya", "KE"],
            "TZA": ["Tanzania", "TZ"],
            "UGA": ["Uganda", "UG"],
            "RWA": ["Rwanda", "RW"],
            "BDI": ["Burundi", "BI"],
            "SSD": ["South Sudan", "SS"],
            "SDN": ["Sudan", "SD"],
            "EGY": ["Egypt", "EG"],
            "LBY": ["Libya", "LY"],
            "TUN": ["Tunisia", "TN"],
            "ALB": ["Albania", "AL"],
            "AND": ["Andorra", "AD"],
            "ARM": ["Armenia", "AM"],
            "AUT": ["Austria", "AT"],
            "AZE": ["Azerbaijan", "AZ"],
            "BLR": ["Belarus", "BY"],
            "BEL": ["Belgium", "BE"],
            "BIH": ["Bosnia and Herzegovina", "BA"],
            "BGR": ["Bulgaria", "BG"],
            "HRV": ["Croatia", "HR"],
            "CYP": ["Cyprus", "CY"],
            "CZE": ["Czech Republic", "CZ"],
            "DNK": ["Denmark", "DK"],
            "EST": ["Estonia", "EE"],
            "FIN": ["Finland", "FI"],
            "FRA": ["France", "FR"],
            "GEO": ["Georgia", "GE"],
            "DEU": ["Germany", "DE"],
            "GRC": ["Greece", "GR"],
            "HUN": ["Hungary", "HU"],
            "ISL": ["Iceland", "IS"],
            "IRL": ["Ireland", "IE"],
            "ITA": ["Italy", "IT"],
            "KAZ": ["Kazakhstan", "KZ"],
            "KOS": ["Kosovo", "XK"],
            "LVA": ["Latvia", "LV"],
            "LIE": ["Liechtenstein", "LI"],
            "LTU": ["Lithuania", "LT"],
            "LUX": ["Luxembourg", "LU"],
            "MLT": ["Malta", "MT"],
            "MDA": ["Moldova", "MD"],
            "MCO": ["Monaco", "MC"],
            "MNE": ["Montenegro", "ME"],
            "NLD": ["Netherlands", "NL"],
            "MKD": ["North Macedonia", "MK"],
            "NOR": ["Norway", "NO"],
            "POL": ["Poland", "PL"],
            "PRT": ["Portugal", "PT"],
            "ROU": ["Romania", "RO"],
            "RUS": ["Russia", "RU"],
            "SMR": ["San Marino", "SM"],
            "SRB": ["Serbia", "RS"],
            "SVK": ["Slovakia", "SK"],
            "SVN": ["Slovenia", "SI"],
            "ESP": ["Spain", "ES"],
            "SWE": ["Sweden", "SE"],
            "CHE": ["Switzerland", "CH"],
            "UKR": ["Ukraine", "UA"],
            "GBR": ["United Kingdom", "UK"],
            "VAT": ["Vatican City", "VA"],
            "ALB": ["Albania", "AL"],
            "DZA": ["Algeria", "DZ"],
            "ASM": ["American Samoa", "AS"],
            "AND": ["Andorra", "AD"],
            "AGO": ["Angola", "AO"],
            "AIA": ["Anguilla", "AI"],
            "ATA": ["Antarctica", "AQ"],
            "ATG": ["Antigua and Barbuda", "AG"],
            "ARG": ["Argentina", "AR"],
            "ARM": ["Armenia", "AM"],
            "ABW": ["Aruba", "AW"],
            "AUS": ["Australia", "AU"],
            "AUT": ["Austria", "AT"],
            "AZE": ["Azerbaijan", "AZ"],
            "BHS": ["Bahamas", "BS"],
            "BHR": ["Bahrain", "BH"],
            "BGD": ["Bangladesh", "BD"],
            "BRB": ["Barbados", "BB"],
            "BLR": ["Belarus", "BY"],
            "BEL": ["Belgium", "BE"],
            "BLZ": ["Belize", "BZ"],
            "BEN": ["Benin", "BJ"],
            "BMU": ["Bermuda", "BM"],
            "BTN": ["Bhutan", "BT"],
            "BOL": ["Bolivia", "BO"],
            "BES": ["Bonaire, Sint Eustatius and Saba", "BQ"],
            "BIH": ["Bosnia and Herzegovina", "BA"],
            "BWA": ["Botswana", "BW"],
            "BVT": ["Bouvet Island", "BV"],
            "BRA": ["Brazil", "BR"],
            "IOT": ["British Indian Ocean Territory", "IO"],
            "BRN": ["Brunei", "BN"],
            "BGR": ["Bulgaria", "BG"],
            "BFA": ["Burkina Faso", "BF"],
            "BDI": ["Burundi", "BI"],
            "KHM": ["Cambodia", "KH"],
            "CMR": ["Cameroon", "CM"],
            "CAN": ["Canada", "CA"],
            "CPV": ["Cape Verde", "CV"],
            "CYM": ["Cayman Islands", "KY"],
            "CAF": ["Central African Republic", "CF"],
            "TCD": ["Chad", "TD"],
            "CHL": ["Chile", "CL"],
            "CHN": ["China", "CN"],
            "CXR": ["Christmas Island", "CX"],
            "CCK": ["Cocos Islands", "CC"],
            "COL": ["Colombia", "CO"],
            "COM": ["Comoros", "KM"],
            "COG": ["Congo", "CG"],
            "COD": ["Congo, Democratic Republic of the", "CD"],
            "COK": ["Cook Islands", "CK"],
            "CRI": ["Costa Rica", "CR"],
            "CIV": ["Côte d'Ivoire", "CI"],
            "HRV": ["Croatia", "HR"],
            "CUB": ["Cuba", "CU"],
            "CUW": ["Curaçao", "CW"],
            "CYP": ["Cyprus", "CY"],
            "CZE": ["Czech Republic", "CZ"],
            "DNK": ["Denmark", "DK"],
            "DJI": ["Djibouti", "DJ"],
            "DMA": ["Dominica", "DM"],
            "DOM": ["Dominican Republic", "DO"],
            "ECU": ["Ecuador", "EC"],
            "EGY": ["Egypt", "EG"],
            "SLV": ["El Salvador", "SV"],
            "GNQ": ["Equatorial Guinea", "GQ"],
            "ERI": ["Eritrea", "ER"],
            "EST": ["Estonia", "EE"],
            "SWZ": ["Eswatini", "SZ"],
            "ETH": ["Ethiopia", "ET"],
            "FLK": ["Falkland Islands", "FK"],
            "FRO": ["Faroe Islands", "FO"],
            "FJI": ["Fiji", "FJ"],
            "FIN": ["Finland", "FI"],
            "FRA": ["France", "FR"],
            "GUF": ["French Guiana", "GF"],
            "PYF": ["French Polynesia", "PF"],
            "ATF": ["French Southern Territories", "TF"],
            "GAB": ["Gabon", "GA"],
            "GMB": ["Gambia", "GM"],
            "GEO": ["Georgia", "GE"],
            "DEU": ["Germany", "DE"],
            "GHA": ["Ghana", "GH"],
            "GIB": ["Gibraltar", "GI"],
            "GRC": ["Greece", "GR"],
            "GRL": ["Greenland", "GL"],
            "GRD": ["Grenada", "GD"],
            "GLP": ["Guadeloupe", "GP"],
            "GUM": ["Guam", "GU"],
            "GTM": ["Guatemala", "GT"],
            "GGY": ["Guernsey", "GG"],
            "GIN": ["Guinea", "GN"],
            "GNB": ["Guinea-Bissau", "GW"],
            "GUY": ["Guyana", "GY"],
            "HTI": ["Haiti", "HT"],
            "HMD": ["Heard Island and McDonald Islands", "HM"],
            "VAT": ["Holy See", "VA"],
            "HND": ["Honduras", "HN"],
            "HKG": ["Hong Kong", "HK"],
            "HUN": ["Hungary", "HU"],
            "ISL": ["Iceland", "IS"],
            "IND": ["India", "IN"],
            "IDN": ["Indonesia", "ID"],
            "IRN": ["Iran", "IR"],
            "IRQ": ["Iraq", "IQ"],
            "IRL": ["Ireland", "IE"],
            "IMN": ["Isle of Man", "IM"],
            "ISR": ["Israel", "IL"],
            "ITA": ["Italy", "IT"],
            "JAM": ["Jamaica", "JM"],
            "JPN": ["Japan", "JP"],
            "JEY": ["Jersey", "JE"],
            "JOR": ["Jordan", "JO"],
            "KAZ": ["Kazakhstan", "KZ"],
            "KEN": ["Kenya", "KE"],
            "KIR": ["Kiribati", "KI"],
            "PRK": ["Korea, North", "KP"],
            "KOR": ["Korea, South", "KR"],
            "KWT": ["Kuwait", "KW"],
            "KGZ": ["Kyrgyzstan", "KG"],
            "LAO": ["Laos", "LA"],
            "LVA": ["Latvia", "LV"],
            "LBN": ["Lebanon", "LB"],
            "LSO": ["Lesotho", "LS"],
            "LBR": ["Liberia", "LR"],
            "LBY": ["Libya", "LY"],
            "LIE": ["Liechtenstein", "LI"],
            "LTU": ["Lithuania", "LT"],
            "LUX": ["Luxembourg", "LU"],
            "MAC": ["Macao", "MO"],
            "MDG": ["Madagascar", "MG"],
            "MWI": ["Malawi", "MW"],
            "MYS": ["Malaysia", "MY"],
            "MDV": ["Maldives", "MV"],
            "MLI": ["Mali", "ML"],
            "MLT": ["Malta", "MT"],
            "MHL": ["Marshall Islands", "MH"],
            "MTQ": ["Martinique", "MQ"],
            "MRT": ["Mauritania", "MR"],
            "MUS": ["Mauritius", "MU"],
            "MYT": ["Mayotte", "YT"],
            "MEX": ["Mexico", "MX"],
            "FSM": ["Micronesia", "FM"],
            "MDA": ["Moldova", "MD"],
            "MCO": ["Monaco", "MC"],
            "MNG": ["Mongolia", "MN"],
            "MNE": ["Montenegro", "ME"],
            "MSR": ["Montserrat", "MS"],
            "MAR": ["Morocco", "MA"],
            "MOZ": ["Mozambique", "MZ"],
            "MMR": ["Myanmar", "MM"],
            "NAM": ["Namibia", "NA"],
            "NRU": ["Nauru", "NR"],
            "NPL": ["Nepal", "NP"],
            "NLD": ["Netherlands", "NL"],
            "NCL": ["New Caledonia", "NC"],
            "NZL": ["New Zealand", "NZ"],
            "NIC": ["Nicaragua", "NI"],
            "NER": ["Niger", "NE"],
            "NGA": ["Nigeria", "NG"],
            "NIU": ["Niue", "NU"],
            "NFK": ["Norfolk Island", "NF"],
            "MNP": ["Northern Mariana Islands", "MP"],
            "NOR": ["Norway", "NO"],
            "OMN": ["Oman", "OM"],
            "PAK": ["Pakistan", "PK"],
            "PLW": ["Palau", "PW"],
            "PSE": ["Palestine", "PS"],
            "PAN": ["Panama", "PA"],
            "PNG": ["Papua New Guinea", "PG"],
            "PRY": ["Paraguay", "PY"],
            "PER": ["Peru", "PE"],
            "PHL": ["Philippines", "PH"],
            "PCN": ["Pitcairn", "PN"],
            "POL": ["Poland", "PL"],
            "PRT": ["Portugal", "PT"],
            "PRI": ["Puerto Rico", "PR"],
            "QAT": ["Qatar", "QA"],
            "REU": ["Réunion", "RE"],
            "ROU": ["Romania", "RO"],
            "RUS": ["Russia", "RU"],
            "RWA": ["Rwanda", "RW"],
            "BLM": ["Saint Barthélemy", "BL"],
            "SHN": ["Saint Helena", "SH"],
            "KNA": ["Saint Kitts and Nevis", "KN"],
            "LCA": ["Saint Lucia", "LC"],
            "MAF": ["Saint Martin", "MF"],
            "SPM": ["Saint Pierre and Miquelon", "PM"],
            "VCT": ["Saint Vincent and the Grenadines", "VC"],
            "WSM": ["Samoa", "WS"],
            "SMR": ["San Marino", "SM"],
            "STP": ["São Tomé and Príncipe", "ST"],
            "SAU": ["Saudi Arabia", "SA"],
            "SEN": ["Senegal", "SN"],
            "SRB": ["Serbia", "RS"],
            "SYC": ["Seychelles", "SC"],
            "SLE": ["Sierra Leone", "SL"],
            "SGP": ["Singapore", "SG"],
            "SXM": ["Sint Maarten", "SX"],
            "SVK": ["Slovakia", "SK"],
            "SVN": ["Slovenia", "SI"],
            "SLB": ["Solomon Islands", "SB"],
            "SOM": ["Somalia", "SO"],
            "ZAF": ["South Africa", "ZA"],
            "SGS": ["South Georgia and the South Sandwich Islands", "GS"],
            "SSD": ["South Sudan", "SS"],
            "ESP": ["Spain", "ES"],
            "LKA": ["Sri Lanka", "LK"],
            "SDN": ["Sudan", "SD"],
            "SUR": ["Suriname", "SR"],
            "SJM": ["Svalbard and Jan Mayen", "SJ"],
            "SWE": ["Sweden", "SE"],
            "CHE": ["Switzerland", "CH"],
            "SYR": ["Syria", "SY"],
            "TWN": ["Taiwan", "TW"],
            "TJK": ["Tajikistan", "TJ"],
            "TZA": ["Tanzania", "TZ"],
            "THA": ["Thailand", "TH"],
            "TLS": ["Timor-Leste", "TL"],
            "TGO": ["Togo", "TG"],
            "TKL": ["Tokelau", "TK"],
            "TON": ["Tonga", "TO"],
            "TTO": ["Trinidad and Tobago", "TT"],
            "TUN": ["Tunisia", "TN"],
            "TUR": ["Turkey", "TR"],
            "TKM": ["Turkmenistan", "TM"],
            "TCA": ["Turks and Caicos Islands", "TC"],
            "TUV": ["Tuvalu", "TV"],
            "UGA": ["Uganda", "UG"],
            "UKR": ["Ukraine", "UA"],
            "ARE": ["United Arab Emirates", "AE"],
            "GBR": ["United Kingdom", "GB"],
            "USA": ["United States", "US"],
            "UMI": ["United States Minor Outlying Islands", "UM"],
            "URY": ["Uruguay", "UY"],
            "UZB": ["Uzbekistan", "UZ"],
            "VUT": ["Vanuatu", "VU"],
            "VEN": ["Venezuela", "VE"],
            "VNM": ["Vietnam", "VN"],
            "VGB": ["Virgin Islands, British", "VG"],
            "VIR": ["Virgin Islands, U.S.", "VI"],
            "WLF": ["Wallis and Futuna", "WF"],
            "ESH": ["Western Sahara", "EH"],
            "YEM": ["Yemen", "YE"],
            "ZMB": ["Zambia", "ZM"],
            "ZWE": ["Zimbabwe", "ZW"]
        }
    
    def clean(self, data: Any, context: CleaningContext) -> CleanResult:
        """Clean and standardize country names and codes."""
        if not isinstance(data, str):
            return CleanResult(data, [])
        
        original_data = data
        operations = []
        
        try:
            # Normalize input
            clean_data = data.strip().upper()
            
            # Find matching country
            result = None
            for iso3, names in self.country_mappings.items():
                if clean_data == iso3:
                    result = iso3
                    break
                elif clean_data in [n.upper() for n in names]:
                    result = iso3
                    break
            
            if result is None:
                # Use DataNormalizer for country normalization
                try:
                    normalized_country, meta = DataNormalizer.normalize_country(data)
                    result = normalized_country
                    operations.append(CleaningOperation(
                        field="country",
                        operation_type=CleaningOperationType.NORMALIZE,
                        description=f"Normalize country using DataNormalizer: {meta}",
                        before_value=original_data,
                        after_value=result
                    ))
                except ValueError:
                    operations.append(CleaningOperation(
                        field="country",
                        operation_type=CleaningOperationType.VALIDATE,
                        description=f"Unknown country: {data}",
                        success=False,
                        error_message=f"Unknown country: {data}"
                    ))
                    return CleanResult(original_data, operations, context)
            
            # Format output
            if self.output_format == "name":
                # Find the primary name for this country
                primary_name = None
                for iso3, names in self.country_mappings.items():
                    if iso3 == result:
                        primary_name = names[0]
                        break
                
                if primary_name:
                    operations.append(CleaningOperation(
                        field="country",
                        operation_type=CleaningOperationType.FORMAT,
                        description=f"Convert to country name: {primary_name}",
                        before_value=result,
                        after_value=primary_name
                    ))
                    result = primary_name
            
            return CleanResult(result, operations, context)
            
        except Exception as e:
            error_op = CleaningOperation(
                field="country",
                operation_type=CleaningOperationType.VALIDATE,
                description=f"Country cleaning failed: {str(e)}",
                success=False,
                error_message=str(e)
            )
            return CleanResult(original_data, [error_op], context)
    
    def validate_config(self) -> List[str]:
        """Validate configuration."""
        errors = []
        if self.output_format not in ["name", "code"]:
            errors.append("output_format must be 'name' or 'code'")
        if not isinstance(self.standardize_names, bool):
            errors.append("standardize_names must be boolean")
        if not isinstance(self.include_alternative_names, bool):
            errors.append("include_alternative_names must be boolean")
        return errors