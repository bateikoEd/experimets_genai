"""
Unit tests for unified preprocessing pipeline.
"""
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_processing.unified_pipeline import UnifiedPreprocessingPipeline


class TestUnifiedPreprocessingPipeline(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample mixed data
        self.sample_data = pd.DataFrame({
            # Numeric features
            'price': [100000, 150000, 200000, 180000, 220000],
            'sqft_living': [1200, 1800, 2400, 2000, 2600],
            'bedrooms': [2, 3, 4, 3, 4],
            'bathrooms': [1.0, 2.0, 2.5, 2.0, 3.0],
            
            # Categorical features
            'condition': ['Good', 'Excellent', 'Fair', 'Good', 'Excellent'],
            'grade': ['Average', 'High', 'Average', 'High', 'Luxury'],
            
            # Text features
            'description': [
                'Beautiful house with modern kitchen',
                'Cozy home in great neighborhood',
                'Spacious family home with garden',
                'Charming house near schools',
                'Luxury home with premium features'
            ]
        })
        
        self.pipeline = UnifiedPreprocessingPipeline()
    
    def test_init_default_params(self):
        """Test initialization with default parameters."""
        pipeline = UnifiedPreprocessingPipeline()
        
        # Check that processors are initialized
        self.assertIsNotNone(pipeline.numeric_processor)
        self.assertIsNotNone(pipeline.categorical_processor)
        self.assertIsNotNone(pipeline.text_processor)
        
        # Check default parameters
        self.assertFalse(pipeline.verbose)
        self.assertIsNone(pipeline.random_state)
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        pipeline = UnifiedPreprocessingPipeline(
            verbose=True,
            random_state=42,
            numeric_params={'imputation_strategy': 'mean'},
            categorical_params={'encoding_method': 'label'},
            text_params={'max_features': 500}
        )
        
        self.assertTrue(pipeline.verbose)
        self.assertEqual(pipeline.random_state, 42)
    
    def test_identify_column_types(self):
        """Test identification of column types."""
        column_types = self.pipeline._identify_column_types(self.sample_data)
        
        self.assertIsInstance(column_types, dict)
        self.assertIn('numeric', column_types)
        self.assertIn('categorical', column_types)
        self.assertIn('text', column_types)
        
        # Check specific column classifications
        numeric_cols = column_types['numeric']
        categorical_cols = column_types['categorical']
        text_cols = column_types['text']
        
        # Numeric columns
        expected_numeric = ['price', 'sqft_living', 'bedrooms', 'bathrooms']
        for col in expected_numeric:
            self.assertIn(col, numeric_cols)
        
        # Categorical columns
        expected_categorical = ['condition', 'grade']
        for col in expected_categorical:
            self.assertIn(col, categorical_cols)
        
        # Text columns
        self.assertIn('description', text_cols)
    
    def test_fit_transform(self):
        """Test fit and transform functionality."""
        # Fit the pipeline
        self.pipeline.fit(self.sample_data)
        
        # Transform the data
        result = self.pipeline.transform(self.sample_data)
        
        # Check result properties
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), len(self.sample_data))
        self.assertGreater(result.shape[1], 0)  # Should have some features
        
        # All values should be numeric after transformation
        for col in result.columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]))
        
        # Check that pipeline is fitted
        self.assertTrue(self.pipeline.is_fitted)
    
    def test_fit_transform_with_target(self):
        """Test fit and transform with target column."""
        # Create data with target
        data_with_target = self.sample_data.copy()
        target_col = 'price'
        
        # Fit and transform excluding target
        pipeline = UnifiedPreprocessingPipeline()
        pipeline.fit(data_with_target, exclude_columns=[target_col])
        result = pipeline.transform(data_with_target)
        
        # Target column should not be in result
        self.assertNotIn(target_col, result.columns)
    
    def test_fit_transform_subset_data(self):
        """Test fit and transform with subset of columns."""
        # Use only some columns
        subset_data = self.sample_data[['sqft_living', 'bedrooms', 'condition']].copy()
        
        self.pipeline.fit(subset_data)
        result = self.pipeline.transform(subset_data)
        
        # Should work with mixed column types
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), len(subset_data))
        
        # All values should be numeric
        for col in result.columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]))
    
    def test_fit_transform_numeric_only(self):
        """Test fit and transform with only numeric columns."""
        numeric_data = self.sample_data[['price', 'sqft_living', 'bedrooms']].copy()
        
        self.pipeline.fit(numeric_data)
        result = self.pipeline.transform(numeric_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape[1], 3)  # Same number of features
    
    def test_fit_transform_categorical_only(self):
        """Test fit and transform with only categorical columns."""
        categorical_data = self.sample_data[['condition', 'grade']].copy()
        
        self.pipeline.fit(categorical_data)
        result = self.pipeline.transform(categorical_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(result.shape[1], 0)  # Should have encoded features
    
    def test_fit_transform_text_only(self):
        """Test fit and transform with only text columns."""
        text_data = self.sample_data[['description']].copy()
        
        self.pipeline.fit(text_data)
        result = self.pipeline.transform(text_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        
        # Should have text features if extraction is enabled
        if self.pipeline.text_processor.extract_features:
            self.assertGreater(result.shape[1], 0)
    
    def test_fit_transform_empty_data(self):
        """Test handling of empty data."""
        empty_data = pd.DataFrame()
        
        self.pipeline.fit(empty_data)
        result = self.pipeline.transform(empty_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
    
    def test_get_feature_names(self):
        """Test getting feature names after transformation."""
        self.pipeline.fit(self.sample_data)
        feature_names = self.pipeline.get_feature_names()
        
        self.assertIsInstance(feature_names, list)
        self.assertGreater(len(feature_names), 0)
        
        # Feature names should match transformed data columns
        result = self.pipeline.transform(self.sample_data)
        self.assertEqual(len(feature_names), result.shape[1])
    
    def test_get_transformation_info(self):
        """Test getting transformation information."""
        self.pipeline.fit(self.sample_data)
        info = self.pipeline.get_transformation_info()
        
        self.assertIsInstance(info, dict)
        self.assertIn('column_types', info)
        self.assertIn('feature_counts', info)
        self.assertIn('total_features', info)
        
        # Check structure
        self.assertIn('numeric', info['column_types'])
        self.assertIn('categorical', info['column_types'])
        self.assertIn('text', info['column_types'])
    
    def test_transform_before_fit_raises_error(self):
        """Test that transform raises error if called before fit."""
        with self.assertRaises(ValueError):
            self.pipeline.transform(self.sample_data)
    
    def test_transform_different_data_structure(self):
        """Test transform with data having different structure than training."""
        # Fit on original data
        self.pipeline.fit(self.sample_data)
        
        # Try to transform data with different columns
        different_data = pd.DataFrame({
            'new_column': [1, 2, 3],
            'another_column': ['A', 'B', 'C']
        })
        
        # Should handle gracefully (might return empty result or raise informative error)
        try:
            result = self.pipeline.transform(different_data)
            # If it doesn't raise an error, check that result is valid
            self.assertIsInstance(result, pd.DataFrame)
        except (ValueError, KeyError):
            # It's acceptable to raise an error for completely different data
            pass
    
    def test_exclude_columns_functionality(self):
        """Test column exclusion functionality."""
        exclude_cols = ['price', 'description']
        
        self.pipeline.fit(self.sample_data, exclude_columns=exclude_cols)
        result = self.pipeline.transform(self.sample_data)
        
        # Excluded columns should not appear in result
        for col in exclude_cols:
            self.assertNotIn(col, result.columns)
    
    def test_verbose_mode(self):
        """Test verbose mode functionality."""
        verbose_pipeline = UnifiedPreprocessingPipeline(verbose=True)
        
        # Should work without errors in verbose mode
        verbose_pipeline.fit(self.sample_data)
        result = verbose_pipeline.transform(self.sample_data)
        
        self.assertIsInstance(result, pd.DataFrame)


if __name__ == '__main__':
    unittest.main()