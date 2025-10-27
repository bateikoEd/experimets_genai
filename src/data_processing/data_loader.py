"""
Data loading and validation utilities for house price prediction.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidator:
    """Validates house price dataset structure and quality."""
    
    # Expected columns and their types
    EXPECTED_SCHEMA = {
        # Numeric features
        'carpet_area': 'numeric',
        'super_area': 'numeric', 
        'built_up_area': 'numeric',
        'plot_area': 'numeric',
        'bathroom': 'numeric',
        'balcony': 'numeric',
        'parking': 'numeric',
        'total_amount': 'numeric',  # Target variable
        'price_per_sqft': 'numeric',
        
        # Categorical features
        'furnishing': 'categorical',
        'property_status': 'categorical',
        'transaction_type': 'categorical',
        'ownership_type': 'categorical',
        'facing': 'categorical',
        'overlooking': 'categorical',
        
        # Text features
        'description': 'text',
        'location': 'text',
        'property_title': 'text',
        'society_name': 'text',
    }
    
    REQUIRED_COLUMNS = ['total_amount', 'carpet_area']  # Minimum required
    
    def __init__(self, target_col: str = 'total_amount'):
        """
        Initialize validator.
        
        Args:
            target_col: Name of the target variable column
        """
        self.target_col = target_col
        
    def validate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate dataset schema and return validation report.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with validation results
        """
        report = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'missing_columns': [],
            'unexpected_columns': [],
            'column_types': {},
            'data_quality': {}
        }
        
        # Check required columns
        missing_required = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_required:
            report['is_valid'] = False
            report['errors'].append(f"Missing required columns: {missing_required}")
            report['missing_columns'].extend(missing_required)
        
        # Check target column
        if self.target_col not in df.columns:
            report['is_valid'] = False
            report['errors'].append(f"Target column '{self.target_col}' not found")
        
        # Check for unexpected columns
        expected_cols = set(self.EXPECTED_SCHEMA.keys())
        actual_cols = set(df.columns)
        unexpected = actual_cols - expected_cols
        if unexpected:
            report['warnings'].append(f"Unexpected columns found: {unexpected}")
            report['unexpected_columns'].extend(unexpected)
        
        # Analyze column types
        for col in df.columns:
            if col in self.EXPECTED_SCHEMA:
                expected_type = self.EXPECTED_SCHEMA[col]
                actual_type = self._infer_column_type(df[col])
                report['column_types'][col] = {
                    'expected': expected_type,
                    'actual': actual_type,
                    'compatible': self._is_type_compatible(expected_type, actual_type)
                }
        
        # Data quality checks
        report['data_quality'] = self._analyze_data_quality(df)
        
        return report
    
    def _infer_column_type(self, series: pd.Series) -> str:
        """Infer the type of a pandas Series."""
        if pd.api.types.is_numeric_dtype(series):
            return 'numeric'
        elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            # Check if it's categorical (limited unique values)
            unique_ratio = series.nunique() / len(series)
            if unique_ratio < 0.05 and series.nunique() < 50:
                return 'categorical'
            else:
                return 'text'
        else:
            return 'unknown'
    
    def _is_type_compatible(self, expected: str, actual: str) -> bool:
        """Check if actual type is compatible with expected type."""
        if expected == actual:
            return True
        # Numeric can be treated as categorical in some cases
        if expected == 'categorical' and actual == 'numeric':
            return True
        return False
    
    def _analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data quality issues."""
        quality = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_values': {},
            'duplicate_rows': df.duplicated().sum(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
        }
        
        # Missing value analysis
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_pct = missing_count / len(df) * 100
            quality['missing_values'][col] = {
                'count': missing_count,
                'percentage': missing_pct
            }
        
        return quality


def load_house_price_data(file_path: str, target_col: str = 'total_amount') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load and validate house price dataset.
    
    Args:
        file_path: Path to the CSV file
        target_col: Name of target variable column
        
    Returns:
        Tuple of (DataFrame, validation_report)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If validation fails critically
    """
    # Check if file exists
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    logger.info(f"Loading data from: {file_path}")
    
    try:
        # Load data
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
        
        # Validate schema
        validator = DataValidator(target_col=target_col)
        validation_report = validator.validate_schema(df)
        
        # Log validation results
        if validation_report['is_valid']:
            logger.info("Data validation passed")
        else:
            logger.error("Data validation failed:")
            for error in validation_report['errors']:
                logger.error(f"  - {error}")
            raise ValueError("Data validation failed. Check the validation report for details.")
        
        # Log warnings
        for warning in validation_report['warnings']:
            logger.warning(warning)
        
        # Log data quality summary
        quality = validation_report['data_quality']
        logger.info(f"Data quality summary:")
        logger.info(f"  - Total rows: {quality['total_rows']:,}")
        logger.info(f"  - Total columns: {quality['total_columns']}")
        logger.info(f"  - Duplicate rows: {quality['duplicate_rows']}")
        logger.info(f"  - Memory usage: {quality['memory_usage_mb']:.2f} MB")
        
        # Log high missing value columns
        high_missing = {col: stats for col, stats in quality['missing_values'].items() 
                       if stats['percentage'] > 20}
        if high_missing:
            logger.warning("Columns with high missing values (>20%):")
            for col, stats in high_missing.items():
                logger.warning(f"  - {col}: {stats['percentage']:.1f}% missing")
        
        return df, validation_report
        
    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing CSV file: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected error loading data: {e}")


def identify_feature_types(df: pd.DataFrame, target_col: str = 'total_amount') -> Dict[str, List[str]]:
    """
    Identify and categorize feature types for preprocessing.
    
    Args:
        df: Input DataFrame
        target_col: Name of target variable (excluded from features)
        
    Returns:
        Dictionary with feature lists by type
    """
    validator = DataValidator()
    feature_types = {
        'numeric': [],
        'categorical': [],
        'text': []
    }
    
    for col in df.columns:
        if col == target_col:
            continue  # Skip target variable
            
        col_type = validator._infer_column_type(df[col])
        if col_type in feature_types:
            feature_types[col_type].append(col)
    
    logger.info("Feature types identified:")
    for ftype, features in feature_types.items():
        logger.info(f"  - {ftype}: {len(features)} features")
        if features:
            logger.info(f"    {features}")
    
    return feature_types


if __name__ == "__main__":
    # Example usage
    try:
        data_path = "data/house_prices.csv"
        df, report = load_house_price_data(data_path)
        
        feature_types = identify_feature_types(df)
        
        print("\nValidation Report:")
        print(f"Valid: {report['is_valid']}")
        if report['errors']:
            print("Errors:", report['errors'])
        if report['warnings']:
            print("Warnings:", report['warnings'])
            
    except Exception as e:
        logger.error(f"Failed to load data: {e}")