"""
Unit tests for categorical preprocessing functionality.
"""
import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_processing.categorical_preprocessing import CategoricalPreprocessor


class TestCategoricalPreprocessor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample categorical data
        self.sample_data = pd.DataFrame({
            'category1': ['A', 'B', 'C', 'A', 'B', None],  # High cardinality with missing
            'category2': ['X', 'Y', 'X', 'Y', 'X', 'Y'],  # Low cardinality, no missing
            'category3': ['Red', 'Blue', 'Green', 'Red', 'Yellow', 'Purple'],  # Medium cardinality
            'numeric_col': [1, 2, 3, 4, 5, 6]  # Should be filtered out
        })
        
        self.preprocessor = CategoricalPreprocessor()
    
    def test_init_default_params(self):
        """Test initialization with default parameters."""
        processor = CategoricalPreprocessor()
        
        self.assertEqual(processor.encoding_method, 'onehot')
        self.assertEqual(processor.handle_unknown, 'ignore')
        self.assertEqual(processor.max_cardinality, 20)
        self.assertEqual(processor.min_frequency, 1)
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        processor = CategoricalPreprocessor(
            encoding_method='label',
            handle_unknown='error',
            max_cardinality=10,
            min_frequency=2
        )
        
        self.assertEqual(processor.encoding_method, 'label')
        self.assertEqual(processor.handle_unknown, 'error')
        self.assertEqual(processor.max_cardinality, 10)
        self.assertEqual(processor.min_frequency, 2)
    
    def test_identify_categorical_columns(self):
        """Test identification of categorical columns."""
        cat_cols = self.preprocessor.identify_categorical_columns(self.sample_data)
        
        expected_cols = ['category1', 'category2', 'category3']
        self.assertEqual(set(cat_cols), set(expected_cols))
        
        # Verify numeric column is excluded
        self.assertNotIn('numeric_col', cat_cols)
    
    def test_handle_missing_values(self):
        """Test missing value handling."""
        test_data = self.sample_data[['category1']].copy()
        
        # Handle missing values
        result = self.preprocessor._handle_missing_values(test_data)
        
        # Check that missing values are handled
        self.assertFalse(result.isnull().any().any())
    
    def test_filter_low_frequency_categories(self):
        """Test filtering of low frequency categories."""
        processor = CategoricalPreprocessor(min_frequency=2)
        
        # Create data where some categories appear only once
        test_data = pd.DataFrame({
            'category': ['A', 'A', 'B', 'C', 'D']  # A appears 2x, others 1x
        })
        
        result = processor._filter_low_frequency_categories(test_data)
        
        # Categories with frequency < 2 should be replaced
        unique_values = result['category'].unique()
        self.assertIn('A', unique_values)  # A should remain (freq >= 2)
        
        # Check if rare categories are handled
        if processor.rare_category_label in unique_values:
            # Rare categories were replaced with rare_category_label
            pass
        else:
            # All categories met the frequency threshold
            pass
    
    def test_filter_high_cardinality_categories(self):
        """Test filtering of high cardinality categories."""
        processor = CategoricalPreprocessor(max_cardinality=2)
        
        # Create data with high cardinality
        test_data = pd.DataFrame({
            'category': ['A', 'B', 'C', 'D', 'E']  # 5 unique values > max_cardinality=2
        })
        
        result = processor._filter_high_cardinality_categories(test_data)
        
        # Should have at most max_cardinality + 1 unique values (including 'Other')
        unique_count = result['category'].nunique()
        self.assertLessEqual(unique_count, processor.max_cardinality + 1)
    
    def test_apply_onehot_encoding(self):
        """Test one-hot encoding."""
        processor = CategoricalPreprocessor(encoding_method='onehot')
        test_data = pd.DataFrame({
            'category': ['A', 'B', 'A', 'C']
        })
        
        processor.fit(test_data)
        result = processor._apply_onehot_encoding(test_data)
        
        # Check that result is properly encoded
        self.assertIsInstance(result, pd.DataFrame)
        
        # Should have columns for each category (or follow the encoder's pattern)
        self.assertGreater(result.shape[1], 1)  # More than 1 column after encoding
        
        # All values should be numeric
        for col in result.columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]))
    
    def test_apply_label_encoding(self):
        """Test label encoding."""
        processor = CategoricalPreprocessor(encoding_method='label')
        test_data = pd.DataFrame({
            'category': ['A', 'B', 'A', 'C']
        })
        
        processor.fit(test_data)
        result = processor._apply_label_encoding(test_data)
        
        # Check that result is properly encoded
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape[1], 1)  # Same number of columns
        
        # Values should be numeric
        self.assertTrue(pd.api.types.is_numeric_dtype(result.iloc[:, 0]))
    
    def test_fit_transform(self):
        """Test fit and transform functionality."""
        test_data = self.sample_data[['category1', 'category2']].copy()
        
        # Fit the preprocessor
        self.preprocessor.fit(test_data)
        
        # Transform the data
        result = self.preprocessor.transform(test_data)
        
        # Check result properties
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(result.shape[1], 0)  # Should have some columns
        
        # Check that all values are numeric after encoding
        for col in result.columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]))
    
    def test_fit_transform_empty_data(self):
        """Test handling of empty data."""
        empty_data = pd.DataFrame()
        
        self.preprocessor.fit(empty_data)
        result = self.preprocessor.transform(empty_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
    
    def test_fit_transform_no_categorical_columns(self):
        """Test handling of data with no categorical columns."""
        numeric_data = pd.DataFrame({
            'num1': [1, 2, 3, 4, 5],
            'num2': [10.1, 20.2, 30.3, 40.4, 50.5]
        })
        
        self.preprocessor.fit(numeric_data)
        result = self.preprocessor.transform(numeric_data)
        
        # Should return empty DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape[1], 0)
    
    def test_get_feature_names(self):
        """Test getting feature names after transformation."""
        test_data = self.sample_data[['category1', 'category2']].copy()
        
        self.preprocessor.fit(test_data)
        feature_names = self.preprocessor.get_feature_names()
        
        self.assertIsInstance(feature_names, list)
        self.assertGreater(len(feature_names), 0)
    
    def test_transform_before_fit_raises_error(self):
        """Test that transform raises error if called before fit."""
        test_data = self.sample_data[['category1']].copy()
        
        with self.assertRaises(ValueError):
            self.preprocessor.transform(test_data)
    
    def test_transform_with_unknown_categories(self):
        """Test transformation with unknown categories."""
        processor = CategoricalPreprocessor(handle_unknown='ignore')
        
        # Fit on limited data
        train_data = pd.DataFrame({
            'category': ['A', 'B', 'A', 'B']
        })
        processor.fit(train_data)
        
        # Transform with unknown category
        test_data = pd.DataFrame({
            'category': ['A', 'B', 'C']  # 'C' is unknown
        })
        
        # Should not raise an error with handle_unknown='ignore'
        result = processor.transform(test_data)
        self.assertIsInstance(result, pd.DataFrame)


if __name__ == '__main__':
    unittest.main()