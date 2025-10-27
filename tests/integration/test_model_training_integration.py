"""
Integration tests for model training workflow.
"""
import unittest
import pandas as pd
import numpy as np
import tempfile
import os
import sys
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_processing.unified_pipeline import UnifiedPreprocessor
from models.trainer import ModelTrainer
from models.persistence import ModelPersistence
from evaluation.evaluator import ModelEvaluator


class TestModelTrainingIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample house price data
        np.random.seed(42)
        n_samples = 100
        
        self.sample_data = pd.DataFrame({
            # Target variable
            'total_amount': np.random.randint(100000, 1000000, n_samples),
            
            # Numeric features
            'carpet_area': np.random.randint(500, 3000, n_samples),
            'super_area': np.random.randint(600, 3500, n_samples),
            'bathroom': np.random.randint(1, 5, n_samples),
            'balcony': np.random.randint(0, 4, n_samples),
            'parking': np.random.randint(0, 3, n_samples),
            
            # Categorical features
            'furnishing': np.random.choice(['Furnished', 'Semi-Furnished', 'Unfurnished'], n_samples),
            'property_status': np.random.choice(['Ready to Move', 'Under Construction'], n_samples),
            'facing': np.random.choice(['North', 'South', 'East', 'West'], n_samples),
            
            # Text feature
            'description': [f'Beautiful {i}-bedroom apartment with modern amenities' for i in range(1, n_samples + 1)]
        })
        
        # Create temporary directory for test artifacts
        self.temp_dir = tempfile.mkdtemp()
        self.model_path = os.path.join(self.temp_dir, 'test_model.joblib')
        self.pipeline_path = os.path.join(self.temp_dir, 'test_pipeline.joblib')
        
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_full_training_pipeline(self):
        """Test complete model training pipeline from data to trained model."""
        # Step 1: Prepare features and target
        target_col = 'total_amount'
        X = self.sample_data.drop(target_col, axis=1)
        y = self.sample_data[target_col]
        
        # Step 2: Preprocessing pipeline
        preprocessor = UnifiedPreprocessor(
            numeric_imputation='median',
            numeric_scaling=True,
            text_max_features=100,
            text_use_ner=False  # Disable for speed
        )
        
        # Fit and transform data
        preprocessor.fit(X)
        X_processed = preprocessor.transform(X)
        
        # Verify preprocessing worked
        self.assertIsInstance(X_processed, pd.DataFrame)
        self.assertGreater(X_processed.shape[1], 0)
        self.assertEqual(len(X_processed), len(y))
        
        # Step 3: Model training
        trainer = ModelTrainer(
            model_type='random_forest',
            hyperparameters={'n_estimators': 10, 'random_state': 42}  # Small for testing
        )
        
        # Train the model
        model, training_history = trainer.train(X_processed, y)
        
        # Verify training results
        self.assertIsNotNone(model)
        self.assertIsInstance(training_history, dict)
        
        # Step 4: Model evaluation
        evaluator = ModelEvaluator()
        
        # Make predictions
        y_pred = model.predict(X_processed)
        
        # Evaluate model
        metrics = evaluator.evaluate_regression(y, y_pred)
        
        # Verify metrics
        self.assertIsInstance(metrics, dict)
        self.assertIn('rmse', metrics)
        self.assertIn('mae', metrics)
        self.assertIn('r2', metrics)
        
        # Metrics should be reasonable (not NaN or infinite)
        for metric_name, metric_value in metrics.items():
            self.assertFalse(np.isnan(metric_value), f"{metric_name} should not be NaN")
            self.assertFalse(np.isinf(metric_value), f"{metric_name} should not be infinite")
    
    def test_model_persistence_integration(self):
        """Test model saving and loading integration."""
        # Train a simple model
        target_col = 'total_amount'
        X = self.sample_data.drop(target_col, axis=1)
        y = self.sample_data[target_col]
        
        # Simple preprocessing (numeric only for speed)
        X_numeric = X.select_dtypes(include=[np.number])
        X_numeric = X_numeric.fillna(X_numeric.median())
        
        # Train model
        trainer = ModelTrainer(
            model_type='linear_regression',
            hyperparameters={}
        )
        
        model, _ = trainer.train(X_numeric, y)
        
        # Test persistence
        persistence = ModelPersistence()
        
        # Save model and preprocessing info
        model_info = {
            'model': model,
            'feature_names': list(X_numeric.columns),
            'target_name': target_col,
            'preprocessing_steps': ['fillna_median'],
            'metrics': {'rmse': 1000.0, 'r2': 0.8}
        }
        
        success = persistence.save_model(model_info, self.model_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.model_path))
        
        # Load model
        loaded_info = persistence.load_model(self.model_path)
        self.assertIsNotNone(loaded_info)
        self.assertIn('model', loaded_info)
        self.assertIn('feature_names', loaded_info)
        
        # Test predictions with loaded model
        loaded_model = loaded_info['model']
        y_pred_original = model.predict(X_numeric)
        y_pred_loaded = loaded_model.predict(X_numeric)
        
        # Predictions should be identical
        np.testing.assert_array_almost_equal(y_pred_original, y_pred_loaded)
    
    def test_preprocessing_pipeline_persistence(self):
        """Test preprocessing pipeline saving and loading."""
        target_col = 'total_amount'
        X = self.sample_data.drop(target_col, axis=1)
        
        # Create and fit preprocessing pipeline
        preprocessor = UnifiedPreprocessor(
            numeric_imputation='mean',
            numeric_scaling=True,
            text_use_ner=False  # Disable for speed
        )
        
        preprocessor.fit(X)
        X_processed = preprocessor.transform(X)
        
        # Save preprocessing pipeline
        persistence = ModelPersistence()
        pipeline_info = {
            'pipeline': preprocessor,
            'feature_names_in': list(X.columns),
            'feature_names_out': preprocessor.get_feature_names(),
            'transformation_info': preprocessor.get_transformation_info()
        }
        
        success = persistence.save_preprocessing_pipeline(pipeline_info, self.pipeline_path)
        self.assertTrue(success)
        
        # Load pipeline
        loaded_pipeline_info = persistence.load_preprocessing_pipeline(self.pipeline_path)
        self.assertIsNotNone(loaded_pipeline_info)
        
        # Test transformation with loaded pipeline
        loaded_pipeline = loaded_pipeline_info['pipeline']
        X_processed_loaded = loaded_pipeline.transform(X)
        
        # Results should be identical
        pd.testing.assert_frame_equal(X_processed, X_processed_loaded)
    
    def test_cross_validation_integration(self):
        """Test cross-validation integration with preprocessing."""
        target_col = 'total_amount'
        X = self.sample_data.drop(target_col, axis=1)
        y = self.sample_data[target_col]
        
        # Use only numeric features for speed
        X_numeric = X.select_dtypes(include=[np.number])
        
        trainer = ModelTrainer(
            model_type='linear_regression',
            hyperparameters={},
            cv_folds=3  # Small number for testing
        )
        
        # Perform cross-validation
        cv_results = trainer.cross_validate(X_numeric, y)
        
        # Verify results
        self.assertIsInstance(cv_results, dict)
        self.assertIn('cv_scores', cv_results)
        self.assertIn('mean_score', cv_results)
        self.assertIn('std_score', cv_results)
        
        # Check that we got the expected number of CV scores
        self.assertEqual(len(cv_results['cv_scores']), 3)
        
        # Scores should be reasonable
        self.assertFalse(np.isnan(cv_results['mean_score']))
        self.assertFalse(np.isnan(cv_results['std_score']))
    
    def test_feature_importance_integration(self):
        """Test feature importance extraction with preprocessing."""
        target_col = 'total_amount'
        X = self.sample_data.drop(target_col, axis=1)
        y = self.sample_data[target_col]
        
        # Preprocessing
        preprocessor = UnifiedPreprocessor(
            numeric_imputation='median',
            numeric_scaling=True,
            text_use_ner=False  # Disable for simplicity
        )
        
        preprocessor.fit(X)
        X_processed = preprocessor.transform(X)
        
        # Train tree-based model (has feature importance)
        trainer = ModelTrainer(
            model_type='random_forest',
            hyperparameters={'n_estimators': 10, 'random_state': 42}
        )
        
        model, _ = trainer.train(X_processed, y)
        
        # Get feature importance
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            feature_names = preprocessor.get_feature_names()
            
            # Verify feature importance
            self.assertEqual(len(importance), len(feature_names))
            self.assertGreater(np.sum(importance), 0)  # Should have some importance
            
            # Create feature importance DataFrame
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': importance
            }).sort_values('importance', ascending=False)
            
            self.assertIsInstance(importance_df, pd.DataFrame)
            self.assertEqual(len(importance_df), len(feature_names))
    
    def test_error_handling_integration(self):
        """Test error handling in integrated workflow."""
        # Test with invalid data
        invalid_data = pd.DataFrame({
            'col1': [None, None, None],
            'col2': ['a', 'b', 'c']
        })
        invalid_target = pd.Series([1, 2, 3])
        
        preprocessor = UnifiedPreprocessor()
        
        # This should handle gracefully
        preprocessor.fit(invalid_data)
        X_processed = preprocessor.transform(invalid_data)
        
        # If no valid features, should return empty or minimal DataFrame
        self.assertIsInstance(X_processed, pd.DataFrame)
        
        # Test model training with insufficient data
        trainer = ModelTrainer(model_type='linear_regression')
        
        if X_processed.shape[1] > 0:
            # Try training with minimal data
            try:
                model, _ = trainer.train(X_processed, invalid_target)
                # If it succeeds, that's fine
                self.assertIsNotNone(model)
            except ValueError:
                # If it fails with ValueError, that's also acceptable
                pass
    
    def test_memory_efficiency_integration(self):
        """Test memory efficiency with larger dataset."""
        # Create larger dataset
        np.random.seed(42)
        n_samples = 1000  # Larger but still manageable for testing
        
        large_data = pd.DataFrame({
            'total_amount': np.random.randint(100000, 1000000, n_samples),
            'feature_1': np.random.randn(n_samples),
            'feature_2': np.random.randn(n_samples),
            'feature_3': np.random.randn(n_samples),
            'category_1': np.random.choice(['A', 'B', 'C'], n_samples),
            'category_2': np.random.choice(['X', 'Y'], n_samples)
        })
        
        target_col = 'total_amount'
        X = large_data.drop(target_col, axis=1)
        y = large_data[target_col]
        
        # Test memory usage during preprocessing
        initial_memory = X.memory_usage(deep=True).sum()
        
        preprocessor = UnifiedPreprocessor(
            text_use_ner=False  # Disable text features
        )
        
        preprocessor.fit(X)
        X_processed = preprocessor.transform(X)
        
        processed_memory = X_processed.memory_usage(deep=True).sum()
        
        # Verify processing completed
        self.assertIsInstance(X_processed, pd.DataFrame)
        self.assertEqual(len(X_processed), len(y))
        
        # Memory usage should be reasonable (not excessive)
        memory_ratio = processed_memory / initial_memory
        self.assertLess(memory_ratio, 10)  # Should not increase by more than 10x


if __name__ == '__main__':
    unittest.main()