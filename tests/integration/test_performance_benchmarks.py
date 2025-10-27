"""
Performance benchmark and regression tests.
"""
import unittest
import pandas as pd
import numpy as np
import time
import tempfile
import os
import sys
import shutil
from pathlib import Path
import psutil
import gc

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_processing.data_loader import load_house_price_data
from data_processing.numeric_preprocessing import NumericPreprocessor
from models.trainer import ModelTrainer
from evaluation.evaluator import ModelEvaluator


class TestPerformanceBenchmarks(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Performance thresholds (adjust based on expected performance)
        self.max_preprocessing_time = 10.0  # seconds
        self.max_training_time = 30.0  # seconds  
        self.max_memory_usage_mb = 500  # MB
        
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Force garbage collection
        gc.collect()
    
    def create_benchmark_dataset(self, n_samples: int = 1000) -> pd.DataFrame:
        """Create a benchmark dataset of specified size."""
        np.random.seed(42)
        
        return pd.DataFrame({
            'total_amount': np.random.randint(100000, 2000000, n_samples),
            'carpet_area': np.random.randint(400, 5000, n_samples),
            'super_area': np.random.randint(500, 6000, n_samples),
            'built_up_area': np.random.randint(450, 5500, n_samples),
            'bathroom': np.random.randint(1, 6, n_samples),
            'balcony': np.random.randint(0, 5, n_samples),
            'parking': np.random.randint(0, 4, n_samples),
            'furnishing': np.random.choice(['Furnished', 'Semi-Furnished', 'Unfurnished'], n_samples),
            'property_status': np.random.choice(['Ready to Move', 'Under Construction', 'New Launch'], n_samples),
            'facing': np.random.choice(['North', 'South', 'East', 'West', 'North-East', 'North-West'], n_samples),
            'overlooking': np.random.choice(['Garden', 'Pool', 'Main Road', 'Park'], n_samples),
        })
    
    def measure_memory_usage(self):
        """Measure current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def test_data_loading_performance(self):
        """Test data loading performance with different dataset sizes."""
        test_sizes = [100, 500, 1000]
        loading_times = {}
        
        for size in test_sizes:
            # Create test dataset
            data = self.create_benchmark_dataset(size)
            data_file = os.path.join(self.temp_dir, f'benchmark_{size}.csv')
            data.to_csv(data_file, index=False)
            
            # Measure loading time
            start_time = time.time()
            df, validation_report = load_house_price_data(data_file)
            loading_time = time.time() - start_time
            
            loading_times[size] = loading_time
            
            # Verify data loaded correctly
            self.assertEqual(len(df), size)
            self.assertTrue(validation_report['is_valid'])
            
            # Performance assertion (should load quickly)
            self.assertLess(loading_time, 5.0, f"Loading {size} rows took {loading_time:.2f}s (>5s)")
        
        # Log performance results
        print("\nData Loading Performance:")
        for size, time_taken in loading_times.items():
            print(f"  {size:,} rows: {time_taken:.3f}s")
    
    def test_preprocessing_performance(self):
        """Test preprocessing performance and memory usage."""
        # Create medium-sized dataset
        data = self.create_benchmark_dataset(2000)
        
        # Measure initial memory
        initial_memory = self.measure_memory_usage()
        
        # Prepare data
        target_col = 'total_amount'
        X = data.drop(target_col, axis=1)
        y = data[target_col]
        
        # Use only numeric features for consistent performance testing
        numeric_features = [col for col in X.columns if X[col].dtype in ['int64', 'float64']]
        X_numeric = X[numeric_features]
        
        # Measure preprocessing performance
        start_time = time.time()
        
        preprocessor = NumericPreprocessor(imputation_strategy='median', scaling=True)
        preprocessor.fit(X_numeric)
        X_processed = preprocessor.transform(X_numeric)
        
        preprocessing_time = time.time() - start_time
        
        # Measure memory after preprocessing
        peak_memory = self.measure_memory_usage()
        memory_increase = peak_memory - initial_memory
        
        # Performance assertions
        self.assertLess(preprocessing_time, self.max_preprocessing_time, 
                       f"Preprocessing took {preprocessing_time:.2f}s (>{self.max_preprocessing_time}s)")
        
        self.assertLess(memory_increase, self.max_memory_usage_mb,
                       f"Memory increase {memory_increase:.1f}MB (>{self.max_memory_usage_mb}MB)")
        
        # Verify output
        self.assertIsInstance(X_processed, np.ndarray)
        self.assertEqual(X_processed.shape[0], len(X_numeric))
        
        print(f"\nPreprocessing Performance:")
        print(f"  Time: {preprocessing_time:.3f}s")
        print(f"  Memory increase: {memory_increase:.1f}MB")
        print(f"  Input shape: {X_numeric.shape}")
        print(f"  Output shape: {X_processed.shape}")
    
    def test_training_performance(self):
        """Test model training performance."""
        # Create training dataset
        data = self.create_benchmark_dataset(1000)
        
        target_col = 'total_amount'
        X = data.drop(target_col, axis=1)
        y = data[target_col]
        
        # Use only numeric features
        numeric_features = [col for col in X.columns if X[col].dtype in ['int64', 'float64']]
        X_numeric = X[numeric_features]
        
        # Preprocess
        preprocessor = NumericPreprocessor(imputation_strategy='median', scaling=True)
        preprocessor.fit(X_numeric)
        X_processed = preprocessor.transform(X_numeric)
        
        # Measure training time
        start_time = time.time()
        
        from sklearn.linear_model import LinearRegression
        trainer = ModelTrainer(cv_folds=3)  # Reduced for speed
        model = LinearRegression()
        
        model_result = trainer.train_single_model(
            name='linear_regression',
            model=model,
            param_grid={},
            X_train=X_processed,
            y_train=y.values
        )
        
        training_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(training_time, self.max_training_time,
                       f"Training took {training_time:.2f}s (>{self.max_training_time}s)")
        
        # Verify training success
        self.assertIsNotNone(model_result)
        self.assertIsNotNone(model_result.model)
        
        print(f"\nTraining Performance:")
        print(f"  Time: {training_time:.3f}s")
        print(f"  CV Mean Score: {model_result.cv_mean:.4f}")
        print(f"  CV Std: {model_result.cv_std:.4f}")
    
    def test_evaluation_performance(self):
        """Test evaluation performance with large prediction sets."""
        # Create evaluation dataset
        n_samples = 5000
        
        # Generate synthetic predictions and true values
        np.random.seed(42)
        y_true = np.random.randint(100000, 2000000, n_samples)
        y_pred = y_true + np.random.normal(0, 50000, n_samples)  # Add some noise
        
        # Measure evaluation time
        start_time = time.time()
        
        evaluator = ModelEvaluator()
        metrics = evaluator.calculate_regression_metrics(y_true, y_pred)
        
        evaluation_time = time.time() - start_time
        
        # Performance assertion (should be very fast)
        self.assertLess(evaluation_time, 1.0, f"Evaluation took {evaluation_time:.3f}s (>1s)")
        
        # Verify metrics calculated
        self.assertIsInstance(metrics, dict)
        self.assertIn('RMSE', metrics)
        self.assertIn('MAE', metrics)
        self.assertIn('R2', metrics)
        
        print(f"\nEvaluation Performance:")
        print(f"  Time: {evaluation_time:.3f}s")
        print(f"  Samples evaluated: {n_samples:,}")
        print(f"  Rate: {n_samples/evaluation_time:,.0f} samples/second")
    
    def test_memory_leak_regression(self):
        """Test for memory leaks in repeated operations."""
        initial_memory = self.measure_memory_usage()
        
        # Perform multiple preprocessing cycles
        for i in range(5):
            data = self.create_benchmark_dataset(500)
            
            target_col = 'total_amount'
            X = data.drop(target_col, axis=1)
            
            numeric_features = [col for col in X.columns if X[col].dtype in ['int64', 'float64']]
            X_numeric = X[numeric_features]
            
            # Preprocessing
            preprocessor = NumericPreprocessor(imputation_strategy='median', scaling=True)
            preprocessor.fit(X_numeric)
            X_processed = preprocessor.transform(X_numeric)
            
            # Force cleanup
            del data, X, X_numeric, X_processed, preprocessor
            gc.collect()
        
        final_memory = self.measure_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (< 50MB)
        self.assertLess(memory_increase, 50.0, 
                       f"Memory increased by {memory_increase:.1f}MB after repeated operations")
        
        print(f"\nMemory Regression Test:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Final memory: {final_memory:.1f}MB")
        print(f"  Increase: {memory_increase:.1f}MB")
    
    def test_scalability_regression(self):
        """Test that processing time scales reasonably with data size."""
        sizes = [100, 500, 1000]
        times = {}
        
        for size in sizes:
            data = self.create_benchmark_dataset(size)
            
            target_col = 'total_amount'
            X = data.drop(target_col, axis=1)
            
            numeric_features = [col for col in X.columns if X[col].dtype in ['int64', 'float64']]
            X_numeric = X[numeric_features]
            
            # Measure preprocessing time
            start_time = time.time()
            
            preprocessor = NumericPreprocessor(imputation_strategy='median', scaling=True)
            preprocessor.fit(X_numeric)
            X_processed = preprocessor.transform(X_numeric)
            
            processing_time = time.time() - start_time
            times[size] = processing_time
        
        # Check scalability (time should not increase dramatically)
        time_100 = times[100]
        time_1000 = times[1000]
        
        # Processing 10x data should not take more than 20x time (reasonable scalability)
        scalability_ratio = time_1000 / time_100
        self.assertLess(scalability_ratio, 20.0,
                       f"Scalability issue: 10x data took {scalability_ratio:.1f}x time")
        
        print(f"\nScalability Test:")
        for size, time_taken in times.items():
            print(f"  {size:,} rows: {time_taken:.3f}s")
        print(f"  Scalability ratio (1000/100): {scalability_ratio:.1f}x")
    
    def test_baseline_performance_regression(self):
        """Test that performance hasn't regressed below baseline."""
        # Define baseline performance expectations
        baselines = {
            'data_loading_per_1k_rows': 1.0,  # seconds
            'preprocessing_per_1k_rows': 2.0,  # seconds
            'linear_regression_training': 5.0,  # seconds for 1k samples
        }
        
        data = self.create_benchmark_dataset(1000)
        data_file = os.path.join(self.temp_dir, 'baseline_test.csv')
        data.to_csv(data_file, index=False)
        
        # Test data loading
        start_time = time.time()
        df, _ = load_house_price_data(data_file)
        loading_time = time.time() - start_time
        
        self.assertLess(loading_time, baselines['data_loading_per_1k_rows'],
                       f"Data loading regression: {loading_time:.3f}s > {baselines['data_loading_per_1k_rows']}s")
        
        # Test preprocessing
        target_col = 'total_amount'
        X = df.drop(target_col, axis=1)
        y = df[target_col]
        
        numeric_features = [col for col in X.columns if X[col].dtype in ['int64', 'float64']]
        X_numeric = X[numeric_features]
        
        start_time = time.time()
        preprocessor = NumericPreprocessor(imputation_strategy='median', scaling=True)
        preprocessor.fit(X_numeric)
        X_processed = preprocessor.transform(X_numeric)
        preprocessing_time = time.time() - start_time
        
        self.assertLess(preprocessing_time, baselines['preprocessing_per_1k_rows'],
                       f"Preprocessing regression: {preprocessing_time:.3f}s > {baselines['preprocessing_per_1k_rows']}s")
        
        print(f"\nBaseline Performance Test:")
        print(f"  Loading: {loading_time:.3f}s (baseline: {baselines['data_loading_per_1k_rows']}s)")
        print(f"  Preprocessing: {preprocessing_time:.3f}s (baseline: {baselines['preprocessing_per_1k_rows']}s)")


if __name__ == '__main__':
    unittest.main(verbosity=2)