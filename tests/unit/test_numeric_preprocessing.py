"""
Unit tests for numeric preprocessing functionality.
"""
import unittest
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.pipeline import Pipeline
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_processing.numeric_preprocessing import NumericPreprocessor


class TestNumericPreprocessor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample numeric data with missing values and outliers
        self.sample_data = pd.DataFrame({
            'feature1': [1.0, 2.0, 3.0, None, 5.0, 100.0],  # Has missing and outlier
            'feature2': [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],  # Clean data
            'feature3': [0.1, 0.2, None, 0.4, None, 0.6],  # Multiple missing
            'non_numeric': ['a', 'b', 'c', 'd', 'e', 'f']  # Should be filtered out
        })
        
        self.preprocessor = NumericPreprocessor()
    
    def test_init_default_params(self):
        """Test initialization with default parameters."""
        processor = NumericPreprocessor()
        
        self.assertEqual(processor.imputation_strategy, 'median')
        self.assertEqual(processor.scaling_method, 'standard')
        self.assertFalse(processor.handle_outliers)
        self.assertEqual(processor.outlier_method, 'iqr')
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        processor = NumericPreprocessor(
            imputation_strategy='mean',
            scaling_method='robust',
            handle_outliers=True,
            outlier_method='zscore'
        )
        
        self.assertEqual(processor.imputation_strategy, 'mean')
        self.assertEqual(processor.scaling_method, 'robust')
        self.assertTrue(processor.handle_outliers)
        self.assertEqual(processor.outlier_method, 'zscore')
    
    def test_identify_numeric_columns(self):
        """Test identification of numeric columns."""
        numeric_cols = self.preprocessor.identify_numeric_columns(self.sample_data)
        
        expected_cols = ['feature1', 'feature2', 'feature3']
        self.assertEqual(set(numeric_cols), set(expected_cols))
        
        # Verify non-numeric column is excluded
        self.assertNotIn('non_numeric', numeric_cols)
    
    def test_detect_outliers_iqr(self):
        """Test outlier detection using IQR method."""
        test_data = pd.Series([1, 2, 3, 4, 5, 100])  # 100 is an outlier
        
        outliers = self.preprocessor._detect_outliers_iqr(test_data)
        
        # Should detect the outlier
        self.assertTrue(outliers.iloc[-1])  # Last value (100) should be outlier
        self.assertFalse(outliers.iloc[0])  # First value should not be outlier
    
    def test_detect_outliers_zscore(self):
        """Test outlier detection using Z-score method."""
        test_data = pd.Series([1, 2, 3, 4, 5, 100])  # 100 is an outlier
        
        outliers = self.preprocessor._detect_outliers_zscore(test_data, threshold=2.0)
        
        # Should detect the outlier
        self.assertTrue(outliers.iloc[-1])  # Last value (100) should be outlier
    
    def test_handle_outliers_removal(self):
        """Test outlier removal."""
        processor = NumericPreprocessor(handle_outliers=True, outlier_method='iqr')
        test_data = self.sample_data[['feature1', 'feature2']].copy()
        
        # Fit and transform
        processor.fit(test_data)
        result = processor.transform(test_data)
        
        # Should have fewer or equal rows due to outlier removal
        self.assertLessEqual(len(result), len(test_data))
    
    def test_create_pipeline_standard(self):
        """Test pipeline creation with standard scaler."""
        processor = NumericPreprocessor(scaling_method='standard')
        
        pipeline = processor._create_pipeline(['feature1', 'feature2'])
        
        self.assertIsInstance(pipeline, Pipeline)
        
        # Check pipeline steps
        step_names = [step[0] for step in pipeline.steps]
        self.assertIn('imputer', step_names)
        self.assertIn('scaler', step_names)
    
    def test_create_pipeline_robust(self):
        """Test pipeline creation with robust scaler."""
        processor = NumericPreprocessor(scaling_method='robust')
        
        pipeline = processor._create_pipeline(['feature1', 'feature2'])
        
        # Check that robust scaler is used
        scaler_step = None
        for name, transformer in pipeline.steps:
            if name == 'scaler':
                scaler_step = transformer
                break
        
        self.assertIsInstance(scaler_step, RobustScaler)
    
    def test_create_pipeline_no_scaling(self):
        """Test pipeline creation without scaling."""
        processor = NumericPreprocessor(scaling_method='none')
        
        pipeline = processor._create_pipeline(['feature1', 'feature2'])
        
        # Should only have imputer step
        step_names = [step[0] for step in pipeline.steps]
        self.assertIn('imputer', step_names)
        self.assertNotIn('scaler', step_names)
    
    def test_fit_transform(self):
        """Test fit and transform functionality."""
        test_data = self.sample_data[['feature1', 'feature2', 'feature3']].copy()
        
        # Fit the preprocessor
        self.preprocessor.fit(test_data)
        
        # Transform the data
        result = self.preprocessor.transform(test_data)
        
        # Check result properties
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape[1], 3)  # Same number of features
        
        # Check that there are no missing values after imputation
        self.assertEqual(result.isnull().sum().sum(), 0)
        
        # Check that numeric columns are properly transformed
        for col in result.columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(result[col]))
    
    def test_fit_transform_empty_data(self):
        """Test handling of empty data."""
        empty_data = pd.DataFrame()
        
        self.preprocessor.fit(empty_data)
        result = self.preprocessor.transform(empty_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
    
    def test_fit_transform_no_numeric_columns(self):
        """Test handling of data with no numeric columns."""
        text_data = pd.DataFrame({
            'text1': ['hello', 'world', 'test'],
            'text2': ['foo', 'bar', 'baz']
        })
        
        self.preprocessor.fit(text_data)
        result = self.preprocessor.transform(text_data)
        
        # Should return empty DataFrame
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape[1], 0)
    
    def test_get_feature_names(self):
        """Test getting feature names after transformation."""
        test_data = self.sample_data[['feature1', 'feature2', 'feature3']].copy()
        
        self.preprocessor.fit(test_data)
        feature_names = self.preprocessor.get_feature_names()
        
        self.assertEqual(len(feature_names), 3)
        self.assertIn('feature1', feature_names)
        self.assertIn('feature2', feature_names)
        self.assertIn('feature3', feature_names)
    
    def test_transform_before_fit_raises_error(self):
        """Test that transform raises error if called before fit."""
        test_data = self.sample_data[['feature1', 'feature2']].copy()
        
        with self.assertRaises(ValueError):
            self.preprocessor.transform(test_data)


if __name__ == '__main__':
    unittest.main()