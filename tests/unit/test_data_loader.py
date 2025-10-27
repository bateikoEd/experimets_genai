"""
Unit tests for data loader functionality.
"""
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path
import tempfile

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_processing.data_loader import DataValidator, load_house_price_data, identify_feature_types


class TestDataValidator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample data with house price columns
        self.valid_data = pd.DataFrame({
            'total_amount': [100000, 150000, 200000, 180000],
            'carpet_area': [1200, 1800, 2400, 2000],
            'super_area': [1400, 2000, 2600, 2200],
            'bathroom': [2, 3, 4, 3],
            'furnishing': ['Unfurnished', 'Semi-Furnished', 'Furnished', 'Semi-Furnished'],
            'description': ['Nice house', 'Beautiful home', 'Spacious', 'Cozy place']
        })
        
        self.validator = DataValidator()
    
    def test_init_default_target(self):
        """Test initialization with default target column."""
        validator = DataValidator()
        self.assertEqual(validator.target_col, 'total_amount')
    
    def test_init_custom_target(self):
        """Test initialization with custom target column."""
        validator = DataValidator(target_col='price')
        self.assertEqual(validator.target_col, 'price')
    
    def test_validate_schema_valid_data(self):
        """Test validation with valid data."""
        report = self.validator.validate_schema(self.valid_data)
        
        self.assertIsInstance(report, dict)
        self.assertIn('is_valid', report)
        self.assertIn('errors', report)
        self.assertIn('warnings', report)
        self.assertTrue(report['is_valid'])
    
    def test_validate_schema_missing_required_columns(self):
        """Test validation with missing required columns."""
        invalid_data = self.valid_data.drop('carpet_area', axis=1)
        report = self.validator.validate_schema(invalid_data)
        
        self.assertFalse(report['is_valid'])
        self.assertTrue(any('carpet_area' in str(error) for error in report['errors']))
    
    def test_validate_schema_missing_target_column(self):
        """Test validation with missing target column."""
        invalid_data = self.valid_data.drop('total_amount', axis=1)
        report = self.validator.validate_schema(invalid_data)
        
        self.assertFalse(report['is_valid'])
        self.assertTrue(any('total_amount' in str(error) for error in report['errors']))
    
    def test_infer_column_type_numeric(self):
        """Test numeric column type inference."""
        numeric_series = pd.Series([1, 2, 3, 4, 5])
        col_type = self.validator._infer_column_type(numeric_series)
        self.assertEqual(col_type, 'numeric')
    
    def test_infer_column_type_categorical(self):
        """Test categorical column type inference."""
        # Create a series with more repetitions to trigger categorical inference
        categorical_series = pd.Series(['A', 'B', 'A', 'B', 'A'] * 20)  # 100 items with low unique ratio
        col_type = self.validator._infer_column_type(categorical_series)
        self.assertEqual(col_type, 'categorical')
    
    def test_infer_column_type_text(self):
        """Test text column type inference."""
        text_series = pd.Series(['This is a long text', 'Another unique text', 'Different content'])
        col_type = self.validator._infer_column_type(text_series)
        self.assertEqual(col_type, 'text')
    
    def test_is_type_compatible(self):
        """Test type compatibility checking."""
        self.assertTrue(self.validator._is_type_compatible('numeric', 'numeric'))
        self.assertTrue(self.validator._is_type_compatible('categorical', 'numeric'))
        self.assertFalse(self.validator._is_type_compatible('numeric', 'text'))
    
    def test_analyze_data_quality(self):
        """Test data quality analysis."""
        # Add some missing values and duplicates
        test_data = self.valid_data.copy()
        test_data.loc[0, 'description'] = None
        test_data = pd.concat([test_data, test_data.iloc[0:1]], ignore_index=True)  # Add duplicate
        
        quality = self.validator._analyze_data_quality(test_data)
        
        self.assertIsInstance(quality, dict)
        self.assertIn('total_rows', quality)
        self.assertIn('duplicate_rows', quality)
        self.assertIn('missing_values', quality)
        self.assertGreater(quality['duplicate_rows'], 0)


class TestLoadHousePriceData(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary CSV file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, 'test_data.csv')
        
        # Valid test data
        self.test_data = pd.DataFrame({
            'total_amount': [100000, 150000, 200000],
            'carpet_area': [1200, 1800, 2400],
            'super_area': [1400, 2000, 2600],
            'bathroom': [2, 3, 4],
            'furnishing': ['Unfurnished', 'Semi-Furnished', 'Furnished'],
            'description': ['Nice house', 'Beautiful home', 'Spacious']
        })
        self.test_data.to_csv(self.temp_file, index=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_load_house_price_data_success(self):
        """Test successful data loading."""
        df, report = load_house_price_data(self.temp_file)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIsInstance(report, dict)
        self.assertEqual(len(df), 3)
        self.assertTrue(report['is_valid'])
    
    def test_load_house_price_data_file_not_found(self):
        """Test handling of non-existent file."""
        with self.assertRaises(FileNotFoundError):
            load_house_price_data('nonexistent_file.csv')
    
    def test_load_house_price_data_invalid_data(self):
        """Test handling of invalid data structure."""
        # Create invalid CSV (missing required columns)
        invalid_file = os.path.join(self.temp_dir, 'invalid_data.csv')
        invalid_data = pd.DataFrame({
            'random_col': [1, 2, 3],
            'another_col': ['A', 'B', 'C']
        })
        invalid_data.to_csv(invalid_file, index=False)
        
        with self.assertRaises(ValueError):
            load_house_price_data(invalid_file)
        
        os.unlink(invalid_file)
    
    def test_load_house_price_data_custom_target(self):
        """Test loading with custom target column."""
        # The validator has hardcoded required columns, so we need to include them
        # while also having our custom target
        custom_data = self.test_data.copy()
        custom_data['price'] = custom_data['total_amount']  # Add custom target
        custom_file = os.path.join(self.temp_dir, 'custom_target.csv')
        custom_data.to_csv(custom_file, index=False)
        
        df, report = load_house_price_data(custom_file, target_col='price')
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(report['is_valid'])
        
        os.unlink(custom_file)


class TestIdentifyFeatureTypes(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_data = pd.DataFrame({
            'total_amount': [100000, 150000, 200000, 180000],  # Target (should be excluded)
            'carpet_area': [1200, 1800, 2400, 2000],  # Numeric
            'bathroom': [2, 3, 4, 3],  # Numeric
            'furnishing': ['Unfurnished', 'Semi-Furnished', 'Furnished', 'Semi-Furnished'],  # Categorical
            'property_status': ['Ready to Move', 'Under Construction', 'Ready to Move', 'Ready to Move'],  # Categorical
            'description': ['Nice house', 'Beautiful home', 'Spacious property', 'Cozy place'],  # Text
            'location': ['Area 1', 'Area 2', 'Area 3', 'Area 1']  # Text/Categorical (depends on implementation)
        })
    
    def test_identify_feature_types_basic(self):
        """Test basic feature type identification."""
        feature_types = identify_feature_types(self.sample_data)
        
        self.assertIsInstance(feature_types, dict)
        self.assertIn('numeric', feature_types)
        self.assertIn('categorical', feature_types)
        self.assertIn('text', feature_types)
        
        # Check that target is excluded
        all_features = feature_types['numeric'] + feature_types['categorical'] + feature_types['text']
        self.assertNotIn('total_amount', all_features)
        
        # Check that some expected features are classified
        self.assertIn('carpet_area', feature_types['numeric'])
        self.assertIn('bathroom', feature_types['numeric'])
    
    def test_identify_feature_types_custom_target(self):
        """Test feature type identification with custom target column."""
        # Rename target column
        data_custom_target = self.sample_data.rename(columns={'total_amount': 'price'})
        
        feature_types = identify_feature_types(data_custom_target, target_col='price')
        
        all_features = feature_types['numeric'] + feature_types['categorical'] + feature_types['text']
        self.assertNotIn('price', all_features)
    
    def test_identify_feature_types_empty_data(self):
        """Test handling of empty data."""
        empty_data = pd.DataFrame()
        
        feature_types = identify_feature_types(empty_data)
        
        self.assertEqual(len(feature_types['numeric']), 0)
        self.assertEqual(len(feature_types['categorical']), 0)
        self.assertEqual(len(feature_types['text']), 0)
    
    def test_identify_feature_types_single_type(self):
        """Test identification with only one feature type."""
        numeric_only_data = pd.DataFrame({
            'total_amount': [100000, 150000, 200000],  # Target
            'area': [1200, 1800, 2400],  # Numeric
            'bathrooms': [2, 3, 4],  # Numeric
            'price_per_sqft': [83.3, 83.3, 83.3]  # Numeric
        })
        
        feature_types = identify_feature_types(numeric_only_data)
        
        self.assertGreater(len(feature_types['numeric']), 0)
        # Other types might be empty
        self.assertIsInstance(feature_types['categorical'], list)
        self.assertIsInstance(feature_types['text'], list)


if __name__ == '__main__':
    unittest.main()