# Examples and Usage Patterns

This document provides comprehensive examples for using the House Price Prediction ML Pipeline.

## Table of Contents

- [Quick Start Example](#quick-start-example)
- [Data Loading and Validation](#data-loading-and-validation)
- [Custom Preprocessing](#custom-preprocessing)
- [Model Training Patterns](#model-training-patterns)
- [Model Evaluation Examples](#model-evaluation-examples)
- [Production Usage](#production-usage)
- [Advanced Workflows](#advanced-workflows)

---

## Quick Start Example

Complete end-to-end example for beginners:

```python
import pandas as pd
from data_processing.data_loader import load_house_price_data
from data_processing.unified_pipeline import UnifiedPreprocessor
from models.trainer import ModelTrainer
from evaluation.evaluator import ModelEvaluator
from sklearn.model_selection import train_test_split

# 1. Load and validate data
df, validation_report = load_house_price_data('data/house_prices.csv')
print(f"Loaded {len(df)} records")
print(f"Validation status: {validation_report['is_valid']}")

# 2. Prepare features and target
target_col = 'total_amount'
X = df.drop(columns=[target_col])
y = df[target_col]

# 3. Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 4. Preprocess features
preprocessor = UnifiedPreprocessor(target_col=target_col)
preprocessor.fit(X_train)
X_train_processed = preprocessor.transform(X_train)
X_test_processed = preprocessor.transform(X_test)

# 5. Train models
trainer = ModelTrainer(cv_folds=5, n_jobs=-1)
results = trainer.train_all_models(X_train_processed, y_train)

# 6. Get best model and evaluate
best_name, best_result = trainer.get_best_model()
predictions = best_result.model.predict(X_test_processed)

# 7. Evaluate performance
evaluator = ModelEvaluator(feature_names=preprocessor.get_feature_names())
metrics = evaluator.calculate_regression_metrics(y_test, predictions)
print(f"Best model: {best_name}")
print(f"RMSE: {metrics['RMSE']:.2f}")
print(f"R²: {metrics['R2']:.4f}")

# 8. Generate evaluation plots
evaluator.plot_predictions(y_test, predictions, save_path='predictions.png')
evaluator.plot_residuals(y_test, predictions, save_path='residuals.png')
```

---

## Data Loading and Validation

### Basic Data Loading

```python
from data_processing.data_loader import load_house_price_data, identify_feature_types

# Load data with custom target column
df, report = load_house_price_data(
    file_path='custom_data.csv',
    target_col='price'
)

# Check validation results
if not report['is_valid']:
    print("Validation errors:")
    for error in report['errors']:
        print(f"  - {error}")
    
    print("Warnings:")
    for warning in report['warnings']:
        print(f"  - {warning}")

# Analyze feature types
feature_types = identify_feature_types(df, target_col='price')
print(f"Numeric features: {len(feature_types['numeric'])}")
print(f"Categorical features: {len(feature_types['categorical'])}")
print(f"Text features: {len(feature_types['text'])}")
```

### Manual Data Validation

```python
from data_processing.data_loader import DataValidator

# Create custom validator
validator = DataValidator(target_col='custom_price')

# Validate dataset
validation_result = validator.validate_schema(df)

# Access detailed validation info
print("Column types:", validation_result['column_types'])
print("Data quality metrics:", validation_result['data_quality'])
print("Missing columns:", validation_result['missing_columns'])
```

---

## Custom Preprocessing

### Numeric Feature Preprocessing

```python
from data_processing.numeric_preprocessing import NumericPreprocessor
import numpy as np

# Create sample numeric data
numeric_features = ['area', 'bedrooms', 'bathrooms', 'age']
X_numeric = df[numeric_features]

# Basic preprocessing
preprocessor = NumericPreprocessor(
    imputation_strategy='median',
    scaling=True
)

# Fit and transform
X_processed = preprocessor.fit_transform(X_numeric)
print(f"Shape after processing: {X_processed.shape}")

# Advanced preprocessing with outlier handling
advanced_preprocessor = NumericPreprocessor(
    imputation_strategy='median',
    scaling=True,
    handle_outliers=True,
    outlier_method='iqr',
    outlier_threshold=1.5
)

X_advanced = advanced_preprocessor.fit_transform(X_numeric)
```

### Categorical Feature Preprocessing

```python
from data_processing.categorical_preprocessing import CategoricalPreprocessor

# Select categorical features
categorical_features = ['furnishing', 'locality', 'property_type']
X_categorical = df[categorical_features]

# One-hot encoding with rare category handling
preprocessor = CategoricalPreprocessor(
    encoding_method='onehot',
    handle_unknown='ignore',
    max_cardinality=15,
    min_frequency=5
)

# Fit and transform
X_encoded = preprocessor.fit_transform(X_categorical)
feature_names = preprocessor.get_feature_names()

print(f"Original categorical features: {X_categorical.shape[1]}")
print(f"After encoding: {X_encoded.shape[1]}")
print(f"New feature names: {feature_names[:10]}...")  # First 10 names
```

### Text Feature Preprocessing

```python
from data_processing.text_preprocessing import TextPreprocessor

# Select text features
text_features = ['description', 'amenities']
X_text = df[text_features]

# TF-IDF with NER extraction
preprocessor = TextPreprocessor(
    extract_features=True,
    max_features=3000,
    extract_ner=True,
    min_df=2,
    max_df=0.95
)

# Transform text to numeric features
X_text_processed = preprocessor.fit_transform(X_text)
print(f"Text features shape: {X_text_processed.shape}")
```

### Unified Preprocessing Pipeline

```python
from data_processing.unified_pipeline import UnifiedPreprocessor

# Custom preprocessing configuration
preprocessor = UnifiedPreprocessor(
    target_col='total_amount',
    numeric_imputation='median',
    numeric_scaling=True,
    categorical_rare_threshold=0.02,  # 2% minimum frequency
    categorical_max_categories=20,
    text_max_features=2000,
    text_use_ner=False,  # Disable NER for speed
    auto_detect_types=True
)

# Fit on training data
preprocessor.fit(X_train)

# Get transformation information
info = preprocessor.get_transformation_info()
print("Preprocessing summary:")
print(f"  Numeric features processed: {len(info['numeric_features'])}")
print(f"  Categorical features processed: {len(info['categorical_features'])}")
print(f"  Text features processed: {len(info['text_features'])}")
print(f"  Total output features: {len(preprocessor.get_feature_names())}")

# Transform data
X_train_processed = preprocessor.transform(X_train)
X_test_processed = preprocessor.transform(X_test)
```

---

## Model Training Patterns

### Single Model Training

```python
from models.trainer import ModelTrainer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

# Initialize trainer
trainer = ModelTrainer(
    cv_folds=10,
    scoring='neg_root_mean_squared_error',
    n_jobs=-1
)

# Train Random Forest with custom hyperparameters
rf_param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 15, 20, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

rf_result = trainer.train_single_model(
    name='custom_random_forest',
    model=RandomForestRegressor(random_state=42),
    param_grid=rf_param_grid,
    X_train=X_train_processed,
    y_train=y_train
)

print(f"Random Forest CV Score: {rf_result.cv_mean:.4f} ± {rf_result.cv_std:.4f}")
print(f"Best parameters: {rf_result.best_params}")
print(f"Training time: {rf_result.training_time:.2f} seconds")
```

### Batch Model Training

```python
# Train all supported models
results = trainer.train_all_models(X_train_processed, y_train)

# Compare results
print("Model Comparison:")
print("-" * 60)
for name, result in results.items():
    print(f"{name:25} | CV: {result.cv_mean:8.4f} ± {result.cv_std:.4f} | Time: {result.training_time:6.2f}s")

# Get top 3 models
sorted_results = sorted(results.items(), 
                       key=lambda x: x[1].cv_mean, 
                       reverse=True)

print("\nTop 3 Models:")
for i, (name, result) in enumerate(sorted_results[:3], 1):
    print(f"{i}. {name}: {result.cv_mean:.4f}")
```

### Custom Model Integration

```python
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV

# Add custom model to trainer
class CustomModelTrainer(ModelTrainer):
    def train_all_models(self, X_train, y_train):
        # Get default results
        results = super().train_all_models(X_train, y_train)
        
        # Add SVM
        svm_param_grid = {
            'C': [0.1, 1, 10],
            'kernel': ['linear', 'rbf'],
            'gamma': ['scale', 'auto']
        }
        
        svm_result = self.train_single_model(
            name='support_vector_machine',
            model=SVR(),
            param_grid=svm_param_grid,
            X_train=X_train,
            y_train=y_train
        )
        
        results['support_vector_machine'] = svm_result
        return results

# Use custom trainer
custom_trainer = CustomModelTrainer(cv_folds=5)
custom_results = custom_trainer.train_all_models(X_train_processed, y_train)
```

---

## Model Evaluation Examples

### Comprehensive Evaluation

```python
from evaluation.evaluator import ModelEvaluator
from evaluation.feature_analyzer import FeatureAnalyzer
import matplotlib.pyplot as plt

# Initialize evaluator with feature names
feature_names = preprocessor.get_feature_names()
evaluator = ModelEvaluator(feature_names=feature_names)

# Get predictions from best model
best_name, best_result = trainer.get_best_model()
y_pred = best_result.model.predict(X_test_processed)

# Calculate comprehensive metrics
metrics = evaluator.calculate_regression_metrics(y_test, y_pred)

print("Regression Metrics:")
print(f"  RMSE: ${metrics['RMSE']:,.2f}")
print(f"  MAE:  ${metrics['MAE']:,.2f}")
print(f"  R²:   {metrics['R2']:.4f}")
print(f"  MAPE: {metrics['MAPE']:.2f}%")
print(f"  Max Error: ${metrics['Max_Error']:,.2f}")

# Generate evaluation plots
fig1 = evaluator.plot_predictions(
    y_test, y_pred, 
    title=f"{best_name} - Predictions vs Actual",
    save_path=f'plots/{best_name}_predictions.png'
)

fig2 = evaluator.plot_residuals(
    y_test, y_pred,
    title=f"{best_name} - Residual Analysis",
    save_path=f'plots/{best_name}_residuals.png'
)

# Generate comprehensive report
report = evaluator.generate_evaluation_report(y_test, y_pred, best_name)
```

### Feature Importance Analysis

```python
# Initialize feature analyzer
analyzer = FeatureAnalyzer(random_state=42)

# Analyze feature importance using multiple methods
importance_df = analyzer.analyze_feature_importance(
    model=best_result.model,
    feature_names=feature_names,
    X_test=X_test_processed,
    y_test=y_test,
    method='both'  # Built-in + permutation importance
)

# Display top features
print("Top 15 Most Important Features:")
print(importance_df.head(15))

# Plot feature importance
fig = analyzer.plot_feature_importance(
    importance_df, 
    top_n=20,
    save_path='plots/feature_importance.png'
)

plt.show()
```

### Model Comparison Dashboard

```python
import pandas as pd
import matplotlib.pyplot as plt

def create_model_comparison_dashboard(results, X_test, y_test, feature_names):
    """Create comprehensive model comparison dashboard"""
    
    evaluator = ModelEvaluator(feature_names=feature_names)
    comparison_data = []
    
    # Evaluate each model
    for name, result in results.items():
        y_pred = result.model.predict(X_test)
        metrics = evaluator.calculate_regression_metrics(y_test, y_pred)
        
        comparison_data.append({
            'Model': name,
            'CV_Score': result.cv_mean,
            'CV_Std': result.cv_std,
            'Test_RMSE': metrics['RMSE'],
            'Test_R2': metrics['R2'],
            'Test_MAE': metrics['MAE'],
            'Training_Time': result.training_time
        })
    
    # Create comparison DataFrame
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df = comparison_df.sort_values('Test_R2', ascending=False)
    
    # Create plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # R² comparison
    axes[0,0].barh(comparison_df['Model'], comparison_df['Test_R2'])
    axes[0,0].set_title('R² Score Comparison')
    axes[0,0].set_xlabel('R² Score')
    
    # RMSE comparison
    axes[0,1].barh(comparison_df['Model'], comparison_df['Test_RMSE'])
    axes[0,1].set_title('RMSE Comparison')
    axes[0,1].set_xlabel('RMSE ($)')
    
    # Training time comparison
    axes[1,0].barh(comparison_df['Model'], comparison_df['Training_Time'])
    axes[1,0].set_title('Training Time Comparison')
    axes[1,0].set_xlabel('Time (seconds)')
    
    # CV Score vs Test R²
    axes[1,1].scatter(comparison_df['CV_Score'], comparison_df['Test_R2'])
    for i, model in enumerate(comparison_df['Model']):
        axes[1,1].annotate(model, 
                          (comparison_df.iloc[i]['CV_Score'], 
                           comparison_df.iloc[i]['Test_R2']))
    axes[1,1].set_xlabel('CV Score')
    axes[1,1].set_ylabel('Test R²')
    axes[1,1].set_title('CV Score vs Test Performance')
    
    plt.tight_layout()
    plt.savefig('plots/model_comparison_dashboard.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return comparison_df

# Create dashboard
comparison_df = create_model_comparison_dashboard(
    results, X_test_processed, y_test, feature_names
)
print(comparison_df)
```

---

## Production Usage

### Model Persistence and Loading

```python
from models.persistence import ModelPersistence, ModelPredictor

# Save trained model with metadata
persistence = ModelPersistence(base_path="production_models/")

model_info = {
    'model': best_result.model,
    'feature_names': feature_names,
    'target_name': 'total_amount',
    'preprocessing_steps': ['numeric_scaling', 'categorical_encoding', 'text_tfidf'],
    'metrics': metrics,
    'training_date': pd.Timestamp.now(),
    'model_version': '1.0.0',
    'hyperparameters': best_result.best_params
}

# Save model and preprocessing pipeline
model_saved = persistence.save_model(model_info, "house_price_model_v1.joblib")
preprocessing_info = {
    'pipeline': preprocessor,
    'feature_names': feature_names,
    'transformation_info': preprocessor.get_transformation_info()
}
preprocessing_saved = persistence.save_preprocessing_pipeline(
    preprocessing_info, "preprocessing_pipeline_v1.joblib"
)

print(f"Model saved: {model_saved}")
print(f"Preprocessing saved: {preprocessing_saved}")
```

### Production Prediction Interface

```python
# Create production predictor
predictor = ModelPredictor(
    model_path="production_models/house_price_model_v1.joblib",
    preprocessing_path="production_models/preprocessing_pipeline_v1.joblib"
)

# Single house prediction
new_house = {
    'carpet_area': 1500,
    'bathroom': 3,
    'bedrooms': 3,
    'furnishing': 'Semi-Furnished',
    'locality': 'Whitefield',
    'property_type': 'Apartment',
    'description': 'Spacious 3BHK apartment with modern amenities'
}

predicted_price = predictor.predict_single(new_house)
print(f"Predicted price: ${predicted_price:,.2f}")

# Batch predictions
new_houses_df = pd.DataFrame([
    {'carpet_area': 1200, 'bathroom': 2, 'bedrooms': 2, 'furnishing': 'Furnished'},
    {'carpet_area': 1800, 'bathroom': 4, 'bedrooms': 4, 'furnishing': 'Unfurnished'},
    {'carpet_area': 900, 'bathroom': 1, 'bedrooms': 1, 'furnishing': 'Semi-Furnished'}
])

batch_predictions = predictor.predict(new_houses_df)
print("Batch predictions:", batch_predictions)
```

### Production API Example

```python
from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Initialize predictor once
predictor = ModelPredictor(
    model_path="production_models/house_price_model_v1.joblib",
    preprocessing_path="production_models/preprocessing_pipeline_v1.joblib"
)

@app.route('/predict', methods=['POST'])
def predict_house_price():
    try:
        # Get JSON data
        data = request.json
        
        # Make prediction
        prediction = predictor.predict_single(data)
        
        # Return result
        return jsonify({
            'success': True,
            'predicted_price': float(prediction),
            'input_data': data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    try:
        # Get JSON data (list of houses)
        data = request.json
        df = pd.DataFrame(data)
        
        # Make predictions
        predictions = predictor.predict(df)
        
        return jsonify({
            'success': True,
            'predictions': predictions.tolist(),
            'count': len(predictions)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Advanced Workflows

### Experiment Tracking with Weights & Biases

```python
from experiment_tracking.enhanced_trainer import EnhancedModelTrainer
import wandb

# Initialize enhanced trainer with W&B integration
enhanced_trainer = EnhancedModelTrainer(
    project_name="house-price-prediction",
    experiment_name="hyperparameter-optimization",
    tags=["grid-search", "production"],
    cv_folds=5,
    n_jobs=-1
)

# Log dataset information
dataset_info = {
    'train_size': len(X_train),
    'test_size': len(X_test),
    'n_features': X_train_processed.shape[1],
    'target_mean': y_train.mean(),
    'target_std': y_train.std(),
    'feature_types': preprocessor.get_transformation_info()
}

enhanced_trainer.log_dataset_info(dataset_info)

# Log preprocessing configuration
preprocessing_config = {
    'numeric_imputation': 'median',
    'scaling_applied': True,
    'categorical_encoding': 'onehot',
    'text_max_features': 5000,
    'outlier_handling': False
}

enhanced_trainer.log_preprocessing_info(preprocessing_config)

# Train models with comprehensive tracking
results = enhanced_trainer.train_all_models_with_tracking(
    X_train_processed, y_train, 
    X_test_processed, y_test
)

# The enhanced trainer automatically logs:
# - Model hyperparameters
# - Cross-validation scores
# - Training time
# - Model artifacts
# - Feature importance plots
# - Evaluation metrics
```

### Automated Feature Engineering

```python
def automated_feature_engineering(df, target_col):
    """
    Automated feature engineering pipeline
    """
    # Create copy for feature engineering
    df_fe = df.copy()
    
    # Identify numeric columns (excluding target)
    numeric_cols = df_fe.select_dtypes(include=['int64', 'float64']).columns
    numeric_cols = [col for col in numeric_cols if col != target_col]
    
    # Create polynomial features for key numeric features
    key_features = ['carpet_area', 'bathroom', 'bedrooms']
    key_features = [f for f in key_features if f in numeric_cols]
    
    if len(key_features) >= 2:
        for i in range(len(key_features)):
            for j in range(i+1, len(key_features)):
                feat1, feat2 = key_features[i], key_features[j]
                # Interaction terms
                df_fe[f'{feat1}_x_{feat2}'] = df_fe[feat1] * df_fe[feat2]
                # Ratio features
                df_fe[f'{feat1}_per_{feat2}'] = df_fe[feat1] / (df_fe[feat2] + 1e-8)
    
    # Create area-based features
    if 'carpet_area' in df_fe.columns and 'bedrooms' in df_fe.columns:
        df_fe['area_per_bedroom'] = df_fe['carpet_area'] / (df_fe['bedrooms'] + 1)
    
    if 'carpet_area' in df_fe.columns and 'bathroom' in df_fe.columns:
        df_fe['area_per_bathroom'] = df_fe['carpet_area'] / (df_fe['bathroom'] + 1)
    
    # Create categorical aggregation features
    if 'locality' in df_fe.columns and target_col in df_fe.columns:
        locality_stats = df_fe.groupby('locality')[target_col].agg(['mean', 'median', 'std']).add_prefix('locality_')
        df_fe = df_fe.merge(locality_stats, left_on='locality', right_index=True, how='left')
    
    # Log feature engineering info
    new_features = [col for col in df_fe.columns if col not in df.columns]
    print(f"Created {len(new_features)} new features:")
    for feat in new_features:
        print(f"  - {feat}")
    
    return df_fe

# Apply automated feature engineering
df_engineered = automated_feature_engineering(df, 'total_amount')

# Retrain with engineered features
X_engineered = df_engineered.drop(columns=['total_amount'])
y_engineered = df_engineered['total_amount']

X_train_eng, X_test_eng, y_train_eng, y_test_eng = train_test_split(
    X_engineered, y_engineered, test_size=0.2, random_state=42
)

# Reprocess with unified pipeline
preprocessor_eng = UnifiedPreprocessor(target_col='total_amount')
preprocessor_eng.fit(X_train_eng)
X_train_eng_processed = preprocessor_eng.transform(X_train_eng)
X_test_eng_processed = preprocessor_eng.transform(X_test_eng)

# Compare performance
trainer_eng = ModelTrainer(cv_folds=5)
results_eng = trainer_eng.train_all_models(X_train_eng_processed, y_train_eng)

print("\nPerformance Comparison (Original vs Engineered Features):")
for name in results.keys():
    original_score = results[name].cv_mean
    engineered_score = results_eng[name].cv_mean
    improvement = engineered_score - original_score
    print(f"{name}: {original_score:.4f} → {engineered_score:.4f} (Δ: {improvement:+.4f})")
```

### Cross-Validation Strategy Analysis

```python
from sklearn.model_selection import (
    KFold, StratifiedKFold, TimeSeriesSplit, 
    RepeatedKFold, cross_val_score
)
import numpy as np

def compare_cv_strategies(model, X, y, n_splits=5):
    """
    Compare different cross-validation strategies
    """
    # Define CV strategies
    cv_strategies = {
        'KFold': KFold(n_splits=n_splits, shuffle=True, random_state=42),
        'RepeatedKFold': RepeatedKFold(n_splits=n_splits, n_repeats=3, random_state=42),
        # 'TimeSeriesSplit': TimeSeriesSplit(n_splits=n_splits),  # If you have temporal data
    }
    
    results = {}
    
    for strategy_name, cv_strategy in cv_strategies.items():
        scores = cross_val_score(
            model, X, y, 
            cv=cv_strategy, 
            scoring='neg_root_mean_squared_error',
            n_jobs=-1
        )
        
        results[strategy_name] = {
            'scores': scores,
            'mean': scores.mean(),
            'std': scores.std(),
            'min': scores.min(),
            'max': scores.max()
        }
    
    # Print comparison
    print("Cross-Validation Strategy Comparison:")
    print("-" * 60)
    for strategy, metrics in results.items():
        print(f"{strategy:15} | Mean: {metrics['mean']:8.4f} ± {metrics['std']:.4f}")
        print(f"{'':<15} | Range: [{metrics['min']:.4f}, {metrics['max']:.4f}]")
        print()
    
    return results

# Compare CV strategies for best model
best_name, best_result = trainer.get_best_model()
cv_comparison = compare_cv_strategies(
    best_result.model, 
    X_train_processed, 
    y_train
)
```

---

This examples document provides comprehensive usage patterns for the House Price Prediction ML Pipeline. Each example includes complete, runnable code that demonstrates different aspects of the system. Use these patterns as starting points for your own implementations and modify them according to your specific requirements.