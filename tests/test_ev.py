"""
Unit tests for model evaluation functionality.
"""
import unittest
import numpy as np
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from evaluation.evaluator import ModelEvaluator


class TestModelEvaluator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)
        
        # Sample data for testing
        self.y_true = np.array([3.0, 5.0, 2.5, 7.0, 4.5])
        self.y_pred = np.array([2.8, 5.2, 2.4, 6.8, 4.7])
        
        # Perfect predictions
        self.y_perfect = np.array([3.0, 5.0, 2.5, 7.0, 4.5])
        
        # Large dataset for performance testing
        self.y_true_large = np.random.randn(1000) * 100 + 500
        self.y_pred_large = self.y_true_large + np.random.randn(1000) * 10
        
        self.evaluator = ModelEvaluator()
    
    def test_init_default_params(self):
        """Test initialization with default parameters."""
        evaluator = ModelEvaluator()
        
        self.assertIsNone(evaluator.feature_names)
    
    def test_init_with_feature_names(self):
        """Test initialization with feature names."""
        feature_names = ['feature_1', 'feature_2', 'feature_3']
        evaluator = ModelEvaluator(feature_names=feature_names)
        
        self.assertEqual(evaluator.feature_names, feature_names)
    
    def test_calculate_regression_metrics_basic(self):
        """Test basic regression metrics calculation."""
        metrics = self.evaluator.calculate_regression_metrics(self.y_true, self.y_pred)
        
        # Check that all expected metrics are present
        expected_metrics = ['RMSE', 'MAE', 'R2', 'MAPE', 'Max_Error', 'Mean_Error']
        for metric in expected_metrics:
            self.assertIn(metric, metrics)
            self.assertIsInstance(metrics[metric], (float, np.floating))
    
    def test_calculate_regression_metrics_perfect_predictions(self):
        """Test metrics with perfect predictions."""
        metrics = self.evaluator.calculate_regression_metrics(self.y_true, self.y_perfect)
        
        # RMSE should be 0
        self.assertAlmostEqual(metrics['RMSE'], 0.0, places=10)
        
        # MAE should be 0
        self.assertAlmostEqual(metrics['MAE'], 0.0, places=10)
        
        # R2 should be 1
        self.assertAlmostEqual(metrics['R2'], 1.0, places=10)
        
        # MAPE should be 0
        self.assertAlmostEqual(metrics['MAPE'], 0.0, places=10)
        
        # Max_Error should be 0
        self.assertAlmostEqual(metrics['Max_Error'], 0.0, places=10)
        
        # Mean_Error should be 0
        self.assertAlmostEqual(metrics['Mean_Error'], 0.0, places=10)
    
    def test_calculate_regression_metrics_rmse(self):
        """Test RMSE calculation."""
        y_true = np.array([3.0, 5.0, 2.5])
        y_pred = np.array([2.8, 5.2, 2.4])
        
        metrics = self.evaluator.calculate_regression_metrics(y_true, y_pred)
        
        # Manual RMSE calculation
        mse = np.mean((y_true - y_pred) ** 2)
        expected_rmse = np.sqrt(mse)
        
        self.assertAlmostEqual(metrics['RMSE'], expected_rmse, places=6)
    
    def test_calculate_regression_metrics_mae(self):
        """Test MAE calculation."""
        y_true = np.array([3.0, 5.0, 2.5])
        y_pred = np.array([2.8, 5.2, 2.4])
        
        metrics = self.evaluator.calculate_regression_metrics(y_true, y_pred)
        
        # Manual MAE calculation
        expected_mae = np.mean(np.abs(y_true - y_pred))
        
        self.assertAlmostEqual(metrics['MAE'], expected_mae, places=6)
    
    def test_calculate_regression_metrics_r2(self):
        """Test R-squared calculation."""
        metrics = self.evaluator.calculate_regression_metrics(self.y_true, self.y_pred)
        
        # Manual R2 calculation
        ss_res = np.sum((self.y_true - self.y_pred) ** 2)
        ss_tot = np.sum((self.y_true - np.mean(self.y_true)) ** 2)
        expected_r2 = 1 - (ss_res / ss_tot)
        
        self.assertAlmostEqual(metrics['R2'], expected_r2, places=6)
        
        # R2 should be between -inf and 1 for reasonable predictions
        self.assertLessEqual(metrics['R2'], 1.0)
    
    def test_calculate_regression_metrics_r2_no_variance(self):
        """Test R2 when y_true has no variance."""
        y_true_constant = np.array([5.0, 5.0, 5.0, 5.0])
        y_pred = np.array([4.9, 5.1, 5.0, 5.2])
        
        metrics = self.evaluator.calculate_regression_metrics(y_true_constant, y_pred)
        
        # When ss_tot is 0, R2 should be 0
        self.assertEqual(metrics['R2'], 0.0)
    
    def test_calculate_regression_metrics_mape(self):
        """Test MAPE calculation."""
        y_true = np.array([100.0, 200.0, 300.0])
        y_pred = np.array([110.0, 190.0, 310.0])
        
        metrics = self.evaluator.calculate_regression_metrics(y_true, y_pred)
        
        # Manual MAPE calculation
        expected_mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        self.assertAlmostEqual(metrics['MAPE'], expected_mape, places=4)
    
    def test_calculate_regression_metrics_mape_with_zeros(self):
        """Test MAPE with zero values in y_true."""
        y_true = np.array([0.0, 100.0, 200.0])
        y_pred = np.array([10.0, 110.0, 190.0])
        
        # Should not raise error due to 1e-8 protection
        metrics = self.evaluator.calculate_regression_metrics(y_true, y_pred)
        
        self.assertIn('MAPE', metrics)
        self.assertIsInstance(metrics['MAPE'], (float, np.floating))
    
    def test_calculate_regression_metrics_max_error(self):
        """Test maximum error calculation."""
        metrics = self.evaluator.calculate_regression_metrics(self.y_true, self.y_pred)
        
        # Manual max error calculation
        expected_max_error = np.max(np.abs(self.y_true - self.y_pred))
        
        self.assertAlmostEqual(metrics['Max_Error'], expected_max_error, places=6)
    
    def test_calculate_regression_metrics_mean_error(self):
        """Test mean error calculation."""
        metrics = self.evaluator.calculate_regression_metrics(self.y_true, self.y_pred)
        
        # Manual mean error calculation
        expected_mean_error = np.mean(self.y_pred - self.y_true)
        
        self.assertAlmostEqual(metrics['Mean_Error'], expected_mean_error, places=6)
    
    def test_calculate_regression_metrics_large_dataset(self):
        """Test metrics calculation with large dataset."""
        metrics = self.evaluator.calculate_regression_metrics(
            self.y_true_large, 
            self.y_pred_large
        )
        
        # Check all metrics are calculated
        self.assertIn('RMSE', metrics)
        self.assertIn('MAE', metrics)
        self.assertIn('R2', metrics)
        
        # R2 should be reasonable for data with small noise
        self.assertGreater(metrics['R2'], 0.5)
    
    def test_calculate_regression_metrics_all_positive(self):
        """Test that all metrics return valid numeric values."""
        metrics = self.evaluator.calculate_regression_metrics(self.y_true, self.y_pred)
        
        for metric_name, metric_value in metrics.items():
            # Check that value is numeric
            self.assertIsInstance(metric_value, (float, np.floating, int))
            
            # Check that value is not NaN
            self.assertFalse(np.isnan(metric_value), 
                           f"{metric_name} is NaN")
    
    def test_calculate_regression_metrics_consistent_results(self):
        """Test that metrics calculation is deterministic."""
        metrics1 = self.evaluator.calculate_regression_metrics(self.y_true, self.y_pred)
        metrics2 = self.evaluator.calculate_regression_metrics(self.y_true, self.y_pred)
        
        for metric_name in metrics1.keys():
            self.assertEqual(metrics1[metric_name], metrics2[metric_name],
                           f"{metric_name} gives inconsistent results")


if __name__ == '__main__':
    unittest.main()