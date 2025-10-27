# Troubleshooting Guide

This guide helps you resolve common issues when working with the House Price Prediction ML Pipeline.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Data Loading Problems](#data-loading-problems)
- [Preprocessing Errors](#preprocessing-errors)
- [Model Training Issues](#model-training-issues)
- [Memory and Performance Problems](#memory-and-performance-problems)
- [Evaluation and Visualization Errors](#evaluation-and-visualization-errors)
- [Production Deployment Issues](#production-deployment-issues)
- [Environment and Dependencies](#environment-and-dependencies)
- [Frequently Asked Questions](#frequently-asked-questions)

---

## Installation Issues

### Issue: Package Installation Fails

**Problem**: `pip install` commands fail or packages not found.

**Solutions**:

1. **Update pip and setuptools**:
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

2. **Use specific package versions**:
   ```bash
   pip install scikit-learn==1.3.0 pandas==2.0.3 numpy==1.24.3
   ```

3. **Install from requirements.txt**:
   ```bash
   pip install -r requirements.txt
   ```

4. **For M1 Mac users** (ARM architecture):
   ```bash
   # Use conda for better compatibility
   conda install scikit-learn pandas numpy matplotlib seaborn
   ```

### Issue: Import Errors After Installation

**Problem**: Modules not found despite successful installation.

**Solutions**:

1. **Check Python environment**:
   ```python
   import sys
   print(sys.path)
   print(sys.executable)
   ```

2. **Verify package installation**:
   ```bash
   pip list | grep scikit-learn
   pip show scikit-learn
   ```

3. **Restart Python interpreter** or Jupyter kernel.

4. **Check for multiple Python installations**:
   ```bash
   which python
   which pip
   ```

---

## Data Loading Problems

### Issue: CSV File Not Found

**Problem**: `FileNotFoundError: [Errno 2] No such file or directory: 'data/house_prices.csv'`

**Solutions**:

1. **Verify file path**:
   ```python
   import os
   print("Current directory:", os.getcwd())
   print("Files in data/:", os.listdir('data/') if os.path.exists('data/') else "data/ not found")
   ```

2. **Use absolute path**:
   ```python
   import os
   file_path = os.path.abspath('data/house_prices.csv')
   df, report = load_house_price_data(file_path)
   ```

3. **Create data directory if missing**:
   ```bash
   mkdir -p data
   ```

### Issue: Data Validation Fails

**Problem**: Validation errors prevent data loading.

**Example Error**:
```
DataValidationError: Missing required columns: ['total_amount']
```

**Solutions**:

1. **Check actual column names**:
   ```python
   import pandas as pd
   df = pd.read_csv('data/house_prices.csv')
   print("Available columns:", df.columns.tolist())
   ```

2. **Map column names if different**:
   ```python
   # If your target column has a different name
   df = df.rename(columns={'price': 'total_amount'})
   ```

3. **Use custom target column name**:
   ```python
   df, report = load_house_price_data(
       'data/house_prices.csv',
       target_col='your_price_column'
   )
   ```

4. **Handle missing columns**:
   ```python
   from data_processing.data_loader import DataValidator
   
   validator = DataValidator(target_col='total_amount')
   report = validator.validate_schema(df)
   
   if not report['is_valid']:
       print("Missing columns:", report['missing_columns'])
       print("Available columns:", df.columns.tolist())
   ```

### Issue: Encoding Problems

**Problem**: `UnicodeDecodeError` when reading CSV files.

**Solutions**:

1. **Specify encoding explicitly**:
   ```python
   df = pd.read_csv('data/house_prices.csv', encoding='utf-8')
   ```

2. **Try different encodings**:
   ```python
   encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
   for encoding in encodings:
       try:
           df = pd.read_csv('data/house_prices.csv', encoding=encoding)
           print(f"Successfully loaded with encoding: {encoding}")
           break
       except UnicodeDecodeError:
           continue
   ```

3. **Use error handling**:
   ```python
   df = pd.read_csv('data/house_prices.csv', encoding='utf-8', errors='replace')
   ```

---

## Preprocessing Errors

### Issue: Memory Error During Preprocessing

**Problem**: `MemoryError` or system becomes unresponsive during preprocessing.

**Solutions**:

1. **Reduce text features dimensionality**:
   ```python
   preprocessor = UnifiedPreprocessor(
       text_max_features=1000,  # Reduce from default 5000
       text_use_ner=False       # Disable NER to save memory
   )
   ```

2. **Process data in chunks**:
   ```python
   def process_in_chunks(df, preprocessor, chunk_size=1000):
       processed_chunks = []
       for i in range(0, len(df), chunk_size):
           chunk = df.iloc[i:i+chunk_size]
           processed_chunk = preprocessor.transform(chunk)
           processed_chunks.append(processed_chunk)
       return np.vstack(processed_chunks)
   ```

3. **Monitor memory usage**:
   ```python
   import psutil
   import os
   
   def print_memory_usage():
       process = psutil.Process(os.getpid())
       memory_mb = process.memory_info().rss / 1024 / 1024
       print(f"Memory usage: {memory_mb:.1f} MB")
   
   print_memory_usage()  # Before preprocessing
   X_processed = preprocessor.transform(X)
   print_memory_usage()  # After preprocessing
   ```

### Issue: Categorical Encoding Errors

**Problem**: `ValueError: Found unknown categories` during transformation.

**Solutions**:

1. **Use `handle_unknown='ignore'`**:
   ```python
   preprocessor = CategoricalPreprocessor(
       encoding_method='onehot',
       handle_unknown='ignore'  # Ignore unknown categories
   )
   ```

2. **Check for new categories in test data**:
   ```python
   # Check what categories are in test but not in train
   for col in categorical_columns:
       train_cats = set(X_train[col].unique())
       test_cats = set(X_test[col].unique())
       new_cats = test_cats - train_cats
       if new_cats:
           print(f"New categories in {col}: {new_cats}")
   ```

3. **Handle rare categories**:
   ```python
   preprocessor = CategoricalPreprocessor(
       min_frequency=5,  # Categories with <5 occurrences become 'rare'
       max_cardinality=20  # Limit number of categories
   )
   ```

### Issue: Text Preprocessing Fails

**Problem**: Errors during text feature extraction or NLP processing.

**Solutions**:

1. **Handle missing text data**:
   ```python
   # Fill missing text with empty string
   df['description'] = df['description'].fillna('')
   df['amenities'] = df['amenities'].fillna('')
   ```

2. **Disable NER if causing issues**:
   ```python
   preprocessor = TextPreprocessor(
       extract_ner=False,  # Disable NER
       extract_features=True
   )
   ```

3. **Reduce text complexity**:
   ```python
   preprocessor = TextPreprocessor(
       max_features=500,    # Reduce vocabulary size
       min_df=5,           # Ignore rare terms
       max_df=0.8          # Ignore too common terms
   )
   ```

4. **Check text data quality**:
   ```python
   # Check for problematic text
   text_cols = ['description', 'amenities']
   for col in text_cols:
       if col in df.columns:
           print(f"Column {col}:")
           print(f"  Missing: {df[col].isna().sum()}")
           print(f"  Empty strings: {(df[col] == '').sum()}")
           print(f"  Sample: {df[col].iloc[0][:100]}...")
   ```

---

## Model Training Issues

### Issue: GridSearchCV Takes Too Long

**Problem**: Hyperparameter tuning runs for hours without completing.

**Solutions**:

1. **Reduce parameter grid size**:
   ```python
   # Instead of large grid
   param_grid = {
       'n_estimators': [50, 100],      # Reduced from [50, 100, 200, 300]
       'max_depth': [5, 10],           # Reduced from [5, 10, 15, 20, None]
       'min_samples_split': [2, 5]     # Reduced from [2, 5, 10]
   }
   ```

2. **Use RandomizedSearchCV**:
   ```python
   from sklearn.model_selection import RandomizedSearchCV
   
   # Modify ModelTrainer to use RandomizedSearchCV
   class FastModelTrainer(ModelTrainer):
       def train_single_model(self, name, model, param_grid, X_train, y_train):
           search = RandomizedSearchCV(
               model, param_grid, 
               n_iter=20,  # Try 20 random combinations
               cv=self.cv_folds, 
               scoring=self.scoring,
               n_jobs=self.n_jobs,
               random_state=self.random_state
           )
           # ... rest of implementation
   ```

3. **Reduce cross-validation folds**:
   ```python
   trainer = ModelTrainer(cv_folds=3, n_jobs=-1)  # Use 3 instead of 5 folds
   ```

4. **Train subset of models**:
   ```python
   # Train only fast models first
   fast_results = {}
   fast_models = ['linear_regression', 'ridge', 'lasso']
   
   for model_name in fast_models:
       if model_name in results:
           fast_results[model_name] = results[model_name]
   ```

### Issue: Model Training Fails with Singular Matrix

**Problem**: `LinAlgError: Singular matrix` during linear model training.

**Solutions**:

1. **Check for multicollinearity**:
   ```python
   import pandas as pd
   
   # Calculate correlation matrix
   corr_matrix = pd.DataFrame(X_train_processed).corr()
   high_corr = (corr_matrix.abs() > 0.95) & (corr_matrix != 1.0)
   
   # Find highly correlated features
   high_corr_pairs = []
   for i in range(len(corr_matrix.columns)):
       for j in range(i+1, len(corr_matrix.columns)):
           if high_corr.iloc[i, j]:
               high_corr_pairs.append((i, j, corr_matrix.iloc[i, j]))
   
   print("Highly correlated features:", high_corr_pairs)
   ```

2. **Add regularization**:
   ```python
   from sklearn.linear_model import Ridge
   
   # Use Ridge instead of LinearRegression
   ridge_model = Ridge(alpha=1.0)  # L2 regularization
   ```

3. **Remove redundant features**:
   ```python
   # Remove features with very low variance
   from sklearn.feature_selection import VarianceThreshold
   
   selector = VarianceThreshold(threshold=0.001)
   X_reduced = selector.fit_transform(X_train_processed)
   ```

### Issue: Models Perform Poorly

**Problem**: All models have very low R² scores or high error rates.

**Solutions**:

1. **Check target variable distribution**:
   ```python
   import matplotlib.pyplot as plt
   
   plt.figure(figsize=(12, 4))
   
   plt.subplot(1, 3, 1)
   plt.hist(y_train, bins=50, alpha=0.7)
   plt.title('Target Distribution')
   plt.xlabel('Price')
   
   plt.subplot(1, 3, 2)
   plt.boxplot(y_train)
   plt.title('Target Boxplot')
   plt.ylabel('Price')
   
   plt.subplot(1, 3, 3)
   plt.hist(np.log1p(y_train), bins=50, alpha=0.7)
   plt.title('Log-transformed Target')
   plt.xlabel('Log(Price + 1)')
   
   plt.tight_layout()
   plt.show()
   ```

2. **Apply target transformation**:
   ```python
   # Log transform target if highly skewed
   y_train_log = np.log1p(y_train)  # log(1 + x)
   y_test_log = np.log1p(y_test)
   
   # Train on transformed target
   results_log = trainer.train_all_models(X_train_processed, y_train_log)
   
   # Transform predictions back
   y_pred_log = best_model.predict(X_test_processed)
   y_pred = np.expm1(y_pred_log)  # exp(x) - 1
   ```

3. **Check for data leakage**:
   ```python
   # Make sure target is not in features
   feature_names = preprocessor.get_feature_names()
   target_col = 'total_amount'
   
   if target_col in feature_names:
       print("WARNING: Target variable found in features!")
   
   # Check for future information
   if 'date' in df.columns:
       print("Check if future information is leaking into features")
   ```

4. **Analyze feature importance**:
   ```python
   from evaluation.feature_analyzer import FeatureAnalyzer
   
   analyzer = FeatureAnalyzer()
   importance_df = analyzer.analyze_feature_importance(
       best_model, feature_names, X_test_processed, y_test
   )
   
   # Check if any features have zero importance
   zero_importance = importance_df[importance_df['importance'] == 0]
   print(f"Features with zero importance: {len(zero_importance)}")
   ```

---

## Memory and Performance Problems

### Issue: Out of Memory During Training

**Problem**: System runs out of memory during model training.

**Solutions**:

1. **Reduce dataset size for initial experiments**:
   ```python
   # Use a sample for initial development
   sample_size = 10000
   df_sample = df.sample(n=min(sample_size, len(df)), random_state=42)
   ```

2. **Use memory-efficient algorithms**:
   ```python
   from sklearn.linear_model import SGDRegressor
   
   # SGD uses less memory for large datasets
   sgd_model = SGDRegressor(random_state=42, max_iter=1000)
   ```

3. **Implement incremental learning**:
   ```python
   def incremental_training(model, X, y, batch_size=1000):
       """Train model incrementally on batches"""
       for i in range(0, len(X), batch_size):
           X_batch = X[i:i+batch_size]
           y_batch = y[i:i+batch_size]
           
           # Partial fit for compatible models
           if hasattr(model, 'partial_fit'):
               model.partial_fit(X_batch, y_batch)
           else:
               # Retrain on accumulated data
               X_accumulated = X[:i+batch_size]
               y_accumulated = y[:i+batch_size]
               model.fit(X_accumulated, y_accumulated)
       
       return model
   ```

4. **Monitor memory usage**:
   ```python
   import psutil
   import gc
   
   def cleanup_memory():
       """Force garbage collection and print memory usage"""
       gc.collect()
       memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
       print(f"Memory usage: {memory_mb:.1f} MB")
   
   cleanup_memory()  # Call periodically
   ```

### Issue: Slow Processing on Large Datasets

**Problem**: Preprocessing or training takes too long.

**Solutions**:

1. **Parallelize processing**:
   ```python
   # Use all CPU cores
   trainer = ModelTrainer(n_jobs=-1)
   
   # Parallel preprocessing (if using sklearn Pipeline)
   from sklearn.pipeline import Pipeline
   pipeline = Pipeline([
       ('preprocessor', preprocessor),
       ('model', model)
   ], memory='cache_dir')  # Cache intermediate results
   ```

2. **Profile bottlenecks**:
   ```python
   import time
   
   def time_function(func, *args, **kwargs):
       start_time = time.time()
       result = func(*args, **kwargs)
       end_time = time.time()
       print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
       return result
   
   # Time each step
   X_processed = time_function(preprocessor.transform, X_train)
   results = time_function(trainer.train_all_models, X_processed, y_train)
   ```

3. **Use faster alternatives**:
   ```python
   # Use LightGBM for faster gradient boosting
   import lightgbm as lgb
   
   lgb_model = lgb.LGBMRegressor(
       n_estimators=100,
       random_state=42,
       n_jobs=-1
   )
   ```

4. **Optimize text processing**:
   ```python
   # Reduce text feature complexity
   text_preprocessor = TextPreprocessor(
       max_features=1000,      # Reduce vocabulary
       extract_ner=False,      # Disable expensive NER
       min_df=5               # Filter rare words
   )
   ```

---

## Evaluation and Visualization Errors

### Issue: Plotting Fails or Displays Incorrectly

**Problem**: Matplotlib plots don't show or raise errors.

**Solutions**:

1. **Set matplotlib backend**:
   ```python
   import matplotlib
   matplotlib.use('Agg')  # For non-interactive backend
   import matplotlib.pyplot as plt
   
   # Or for interactive plots
   # matplotlib.use('TkAgg')
   ```

2. **Check display settings**:
   ```python
   # For Jupyter notebooks
   %matplotlib inline
   
   # For better quality plots
   %config InlineBackend.figure_format = 'retina'
   ```

3. **Handle missing directories**:
   ```python
   import os
   
   save_path = 'plots/predictions.png'
   os.makedirs(os.path.dirname(save_path), exist_ok=True)
   
   fig = evaluator.plot_predictions(y_test, y_pred, save_path=save_path)
   ```

4. **Fix font issues**:
   ```python
   import matplotlib.pyplot as plt
   
   # Use default fonts if custom fonts cause issues
   plt.rcParams['font.family'] = 'DejaVu Sans'
   
   # Or clear font cache
   import matplotlib.font_manager
   matplotlib.font_manager._rebuild()
   ```

### Issue: Evaluation Metrics Seem Wrong

**Problem**: Metrics don't match expectations or show impossible values.

**Solutions**:

1. **Check data types and scales**:
   ```python
   print("y_test type:", type(y_test), "shape:", getattr(y_test, 'shape', 'N/A'))
   print("y_pred type:", type(y_pred), "shape:", getattr(y_pred, 'shape', 'N/A'))
   print("y_test range:", np.min(y_test), "to", np.max(y_test))
   print("y_pred range:", np.min(y_pred), "to", np.max(y_pred))
   ```

2. **Handle transformed targets**:
   ```python
   # If you log-transformed the target, transform back
   if target_was_log_transformed:
       y_test_original = np.expm1(y_test)
       y_pred_original = np.expm1(y_pred)
       metrics = evaluator.calculate_regression_metrics(y_test_original, y_pred_original)
   ```

3. **Check for infinite or NaN values**:
   ```python
   print("y_test NaN count:", np.isnan(y_test).sum())
   print("y_pred NaN count:", np.isnan(y_pred).sum())
   print("y_test infinite count:", np.isinf(y_test).sum())
   print("y_pred infinite count:", np.isinf(y_pred).sum())
   
   # Remove invalid values
   valid_mask = ~(np.isnan(y_test) | np.isnan(y_pred) | np.isinf(y_test) | np.isinf(y_pred))
   y_test_clean = y_test[valid_mask]
   y_pred_clean = y_pred[valid_mask]
   ```

---

## Production Deployment Issues

### Issue: Model Loading Fails in Production

**Problem**: Saved model cannot be loaded or predictions fail.

**Solutions**:

1. **Version compatibility check**:
   ```python
   import joblib
   import sklearn
   
   # Check versions when saving
   model_info = {
       'model': trained_model,
       'sklearn_version': sklearn.__version__,
       'python_version': sys.version,
       'save_date': pd.Timestamp.now()
   }
   joblib.dump(model_info, 'model_with_metadata.joblib')
   
   # Check compatibility when loading
   loaded_info = joblib.load('model_with_metadata.joblib')
   if loaded_info['sklearn_version'] != sklearn.__version__:
       print(f"WARNING: Version mismatch! Saved with {loaded_info['sklearn_version']}, running {sklearn.__version__}")
   ```

2. **Test model loading separately**:
   ```python
   # Test loading immediately after saving
   try:
       test_loaded = joblib.load('model.joblib')
       test_prediction = test_loaded.predict(X_test[:1])
       print("Model loading test: SUCCESS")
   except Exception as e:
       print(f"Model loading test: FAILED - {e}")
   ```

3. **Use pickle protocol compatibility**:
   ```python
   import pickle
   
   # Save with specific protocol for compatibility
   joblib.dump(model, 'model.joblib', protocol=pickle.HIGHEST_PROTOCOL)
   ```

### Issue: Inconsistent Predictions Between Training and Production

**Problem**: Same input gives different predictions in production.

**Solutions**:

1. **Verify preprocessing consistency**:
   ```python
   # Save preprocessing state
   preprocessing_info = {
       'pipeline': preprocessor,
       'feature_names_in': X_train.columns.tolist(),
       'feature_names_out': preprocessor.get_feature_names(),
       'transformation_info': preprocessor.get_transformation_info()
   }
   
   # In production, check preprocessing
   def verify_preprocessing(new_data, preprocessing_info):
       expected_features = preprocessing_info['feature_names_in']
       actual_features = new_data.columns.tolist()
       
       missing = set(expected_features) - set(actual_features)
       extra = set(actual_features) - set(expected_features)
       
       if missing:
           print(f"Missing features: {missing}")
       if extra:
           print(f"Extra features: {extra}")
       
       return len(missing) == 0 and len(extra) == 0
   ```

2. **Test with known examples**:
   ```python
   # Save test cases during training
   test_cases = {
       'input': X_test.iloc[:5].to_dict('records'),
       'expected_output': y_pred[:5].tolist()
   }
   joblib.dump(test_cases, 'test_cases.joblib')
   
   # In production, run test cases
   def validate_model_consistency(predictor, test_cases, tolerance=1e-6):
       for i, (input_data, expected) in enumerate(zip(test_cases['input'], test_cases['expected_output'])):
           actual = predictor.predict_single(input_data)
           diff = abs(actual - expected)
           if diff > tolerance:
               print(f"Test case {i}: Expected {expected}, got {actual}, diff: {diff}")
               return False
       return True
   ```

---

## Environment and Dependencies

### Issue: Conflicting Package Versions

**Problem**: Different packages require incompatible versions of dependencies.

**Solutions**:

1. **Use virtual environment**:
   ```bash
   # Create fresh environment
   python -m venv house_price_env
   source house_price_env/bin/activate  # On Windows: house_price_env\Scripts\activate
   
   # Install packages
   pip install -r requirements.txt
   ```

2. **Use conda environment**:
   ```bash
   conda create -n house_price python=3.9
   conda activate house_price
   conda install scikit-learn pandas numpy matplotlib seaborn
   pip install wandb  # For packages not in conda
   ```

3. **Pin exact versions**:
   ```bash
   # Generate exact requirements
   pip freeze > requirements_exact.txt
   
   # Install exact versions
   pip install -r requirements_exact.txt
   ```

4. **Use dependency resolution tools**:
   ```bash
   # Use pip-tools for better dependency management
   pip install pip-tools
   
   # Create requirements.in with high-level dependencies
   # scikit-learn>=1.0.0
   # pandas>=1.3.0
   
   # Generate locked requirements
   pip-compile requirements.in
   ```

### Issue: Jupyter Kernel Problems

**Problem**: Jupyter notebook can't find installed packages.

**Solutions**:

1. **Install ipykernel in environment**:
   ```bash
   pip install ipykernel
   python -m ipykernel install --user --name=house_price --display-name="House Price ML"
   ```

2. **Check kernel environment**:
   ```python
   # In notebook cell
   import sys
   print("Python executable:", sys.executable)
   print("Python path:", sys.path)
   
   # Verify packages
   import sklearn
   print("Scikit-learn version:", sklearn.__version__)
   ```

3. **Restart kernel and clear output**:
   - Kernel → Restart & Clear Output
   - Re-run all cells

---

## Frequently Asked Questions

### Q: How do I handle missing values in categorical features?

**A**: The `CategoricalPreprocessor` handles missing values by treating them as a separate category:

```python
# Missing values automatically become 'missing' category
preprocessor = CategoricalPreprocessor(encoding_method='onehot')

# Or fill missing values explicitly before preprocessing
df['category_col'] = df['category_col'].fillna('unknown')
```

### Q: Can I use my own custom features?

**A**: Yes, add features before preprocessing:

```python
# Add custom features
df['price_per_sqft'] = df['total_amount'] / df['carpet_area']
df['room_ratio'] = df['bedrooms'] / df['bathroom']

# Then use unified preprocessor
preprocessor = UnifiedPreprocessor(target_col='total_amount')
```

### Q: How do I handle very large datasets?

**A**: Use chunking and incremental processing:

```python
def process_large_dataset(file_path, chunk_size=10000):
    results = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        processed_chunk = preprocessor.transform(chunk)
        results.append(processed_chunk)
    return np.vstack(results)
```

### Q: What if my target variable is categorical?

**A**: Modify the pipeline for classification:

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Use classification metrics
def evaluate_classification(y_true, y_pred):
    accuracy = accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred)
    return {'accuracy': accuracy, 'report': report}
```

### Q: How do I add new models to the trainer?

**A**: Extend the `ModelTrainer` class:

```python
class ExtendedModelTrainer(ModelTrainer):
    def get_model_configs(self):
        configs = super().get_model_configs()
        
        # Add new model
        configs['xgboost'] = {
            'model': XGBRegressor(random_state=self.random_state),
            'param_grid': {
                'n_estimators': [100, 200],
                'max_depth': [3, 6, 9],
                'learning_rate': [0.01, 0.1, 0.2]
            }
        }
        
        return configs
```

### Q: How do I debug preprocessing issues?

**A**: Use the transformation info and intermediate outputs:

```python
# Get detailed preprocessing info
info = preprocessor.get_transformation_info()
print("Preprocessing details:", info)

# Check intermediate steps
preprocessor.fit(X_train)
X_numeric = preprocessor._get_numeric_features(X_train)
X_categorical = preprocessor._get_categorical_features(X_train)
print("Numeric shape:", X_numeric.shape)
print("Categorical shape:", X_categorical.shape)
```

### Q: Can I use this pipeline with time series data?

**A**: Yes, but modify the cross-validation strategy:

```python
from sklearn.model_selection import TimeSeriesSplit

class TimeSeriesModelTrainer(ModelTrainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cv = TimeSeriesSplit(n_splits=self.cv_folds)
```

---

## Getting Additional Help

If you're still experiencing issues:

1. **Check the GitHub Issues**: Look for similar problems and solutions
2. **Enable Debug Logging**: Add logging to see detailed execution:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
3. **Create Minimal Reproducible Example**: Isolate the problem with minimal code
4. **Check Documentation**: Review the API documentation for parameter details
5. **Contact Support**: Create a GitHub issue with:
   - Complete error message
   - Python version and package versions
   - Operating system
   - Minimal code to reproduce the issue

Remember to always backup your data and models before trying fixes!