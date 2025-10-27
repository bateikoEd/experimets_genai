# API Documentation

This document provides comprehensive API documentation for the House Price Prediction ML Pipeline.

## Table of Contents

- [Data Processing](#data-processing)
- [Model Training](#model-training)
- [Model Evaluation](#model-evaluation)
- [Model Persistence](#model-persistence)
- [Experiment Tracking](#experiment-tracking)

---

## Data Processing

### `data_processing.data_loader`

#### `DataValidator`

**Purpose**: Validates house price dataset structure and quality.

**Class Definition**:
```python
class DataValidator:
    def __init__(self, target_col: str = 'total_amount')
```

**Key Methods**:

##### `validate_schema(df: pd.DataFrame) -> Dict[str, Any]`

Validates dataset schema and returns validation report.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame to validate

**Returns**:
- `Dict[str, Any]`: Validation report with keys:
  - `is_valid` (bool): Overall validation status
  - `errors` (List[str]): List of validation errors
  - `warnings` (List[str]): List of warnings
  - `missing_columns` (List[str]): Missing required columns
  - `column_types` (Dict): Column type analysis
  - `data_quality` (Dict): Data quality metrics

**Example**:
```python
validator = DataValidator(target_col='total_amount')
report = validator.validate_schema(df)
if report['is_valid']:
    print("Data validation passed")
else:
    print("Errors:", report['errors'])
```

#### `load_house_price_data(file_path: str, target_col: str = 'total_amount')`

**Purpose**: Loads and validates house price dataset.

**Parameters**:
- `file_path` (str): Path to the CSV file
- `target_col` (str): Name of target variable column

**Returns**:
- `Tuple[pd.DataFrame, Dict[str, Any]]`: DataFrame and validation report

**Raises**:
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If validation fails critically

**Example**:
```python
df, report = load_house_price_data('data/house_prices.csv')
```

#### `identify_feature_types(df: pd.DataFrame, target_col: str = 'total_amount')`

**Purpose**: Identifies and categorizes feature types for preprocessing.

**Parameters**:
- `df` (pd.DataFrame): Input DataFrame
- `target_col` (str): Name of target variable (excluded from features)

**Returns**:
- `Dict[str, List[str]]`: Dictionary with feature lists by type:
  - `numeric`: List of numeric feature names
  - `categorical`: List of categorical feature names
  - `text`: List of text feature names

**Example**:
```python
feature_types = identify_feature_types(df)
print("Numeric features:", feature_types['numeric'])
print("Categorical features:", feature_types['categorical'])
print("Text features:", feature_types['text'])
```

### `data_processing.numeric_preprocessing`

#### `NumericPreprocessor`

**Purpose**: Custom transformer for numeric feature preprocessing with missing value imputation and feature scaling.

**Class Definition**:
```python
class NumericPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, 
                 imputation_strategy: str = 'median',
                 scaling: bool = True,
                 handle_outliers: bool = False,
                 outlier_method: str = 'iqr',
                 outlier_threshold: float = 3.0)
```

**Parameters**:
- `imputation_strategy` (str): Strategy for imputing missing values ('median', 'mean', 'constant')
- `scaling` (bool): Whether to apply StandardScaler
- `handle_outliers` (bool): Whether to clip outliers
- `outlier_method` (str): Method for outlier detection ('iqr', 'zscore')
- `outlier_threshold` (float): Threshold for outlier detection

**Key Methods**:

##### `fit(X: Union[pd.DataFrame, np.ndarray]) -> self`

Fits the numeric preprocessor on training data.

##### `transform(X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray`

Transforms input data using fitted preprocessor.

**Example**:
```python
preprocessor = NumericPreprocessor(
    imputation_strategy='median',
    scaling=True,
    handle_outliers=True
)

# Fit on training data
preprocessor.fit(X_train_numeric)

# Transform training and test data
X_train_processed = preprocessor.transform(X_train_numeric)
X_test_processed = preprocessor.transform(X_test_numeric)
```

### `data_processing.categorical_preprocessing`

#### `CategoricalPreprocessor`

**Purpose**: Handles categorical feature preprocessing with encoding and rare category management.

**Class Definition**:
```python
class CategoricalPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self,
                 encoding_method: str = 'onehot',
                 handle_unknown: str = 'ignore',
                 max_cardinality: int = 20,
                 min_frequency: int = 1)
```

**Parameters**:
- `encoding_method` (str): Encoding method ('onehot', 'label')
- `handle_unknown` (str): How to handle unknown categories ('ignore', 'error')
- `max_cardinality` (int): Maximum number of categories per feature
- `min_frequency` (int): Minimum frequency for category inclusion

**Key Methods**:

##### `fit(X: pd.DataFrame) -> self`

Fits the categorical preprocessor.

##### `transform(X: pd.DataFrame) -> pd.DataFrame`

Transforms categorical data.

##### `get_feature_names() -> List[str]`

Returns feature names after transformation.

**Example**:
```python
preprocessor = CategoricalPreprocessor(
    encoding_method='onehot',
    handle_unknown='ignore',
    max_cardinality=15
)

preprocessor.fit(X_train_categorical)
X_processed = preprocessor.transform(X_train_categorical)
feature_names = preprocessor.get_feature_names()
```

### `data_processing.text_preprocessing`

#### `TextPreprocessor`

**Purpose**: Processes text features with TF-IDF vectorization and NER feature extraction.

**Class Definition**:
```python
class TextPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self,
                 extract_features: bool = True,
                 max_features: int = 1000,
                 extract_ner: bool = True,
                 min_df: int = 1,
                 max_df: float = 1.0)
```

**Parameters**:
- `extract_features` (bool): Whether to extract TF-IDF features
- `max_features` (int): Maximum number of TF-IDF features
- `extract_ner` (bool): Whether to extract NER features
- `min_df` (int): Minimum document frequency for TF-IDF
- `max_df` (float): Maximum document frequency for TF-IDF

**Key Methods**:

##### `fit(X: pd.DataFrame) -> self`

Fits the text preprocessor.

##### `transform(X: pd.DataFrame) -> pd.DataFrame`

Transforms text data into numeric features.

**Example**:
```python
preprocessor = TextPreprocessor(
    max_features=5000,
    extract_ner=True,
    min_df=2
)

preprocessor.fit(X_train_text)
X_processed = preprocessor.transform(X_train_text)
```

### `data_processing.unified_pipeline`

#### `UnifiedPreprocessor`

**Purpose**: Unified preprocessing pipeline combining numeric, categorical, and text features.

**Class Definition**:
```python
class UnifiedPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self,
                 target_col: str = 'total_amount',
                 numeric_imputation: str = 'median',
                 numeric_scaling: bool = True,
                 categorical_rare_threshold: float = 0.01,
                 categorical_max_categories: Optional[int] = None,
                 text_max_features: int = 5000,
                 text_use_ner: bool = True,
                 auto_detect_types: bool = True)
```

**Key Methods**:

##### `fit(X: pd.DataFrame, y=None) -> self`

Fits the unified preprocessor on all feature types.

##### `transform(X: pd.DataFrame) -> pd.DataFrame`

Transforms all features using appropriate preprocessing.

##### `get_feature_names() -> List[str]`

Returns all feature names after transformation.

##### `get_transformation_info() -> Dict[str, Any]`

Returns detailed information about the transformation.

**Example**:
```python
preprocessor = UnifiedPreprocessor(
    numeric_imputation='median',
    text_max_features=3000,
    text_use_ner=False
)

preprocessor.fit(X_train)
X_processed = preprocessor.transform(X_train)
feature_names = preprocessor.get_feature_names()
info = preprocessor.get_transformation_info()
```

---

## Model Training

### `models.trainer`

#### `ModelResult`

**Purpose**: Container for model training results.

**Dataclass Definition**:
```python
@dataclass
class ModelResult:
    name: str
    model: Any
    cv_scores: np.ndarray
    cv_mean: float
    cv_std: float
    training_time: float
    best_params: Optional[Dict] = None
    test_score: Optional[float] = None
```

#### `ModelTrainer`

**Purpose**: Comprehensive model training framework for regression tasks.

**Class Definition**:
```python
class ModelTrainer:
    def __init__(self, 
                 cv_folds: int = 5,
                 random_state: int = 42,
                 scoring: str = 'neg_mean_squared_error',
                 n_jobs: int = -1)
```

**Key Methods**:

##### `train_single_model(name: str, model: Any, param_grid: Dict, X_train: np.ndarray, y_train: np.ndarray) -> ModelResult`

Trains a single model with hyperparameter tuning.

**Parameters**:
- `name` (str): Model name for identification
- `model` (Any): Sklearn model instance
- `param_grid` (Dict): Hyperparameter grid for GridSearchCV
- `X_train` (np.ndarray): Training features
- `y_train` (np.ndarray): Training targets

**Returns**:
- `ModelResult`: Training results with model, scores, and metadata

##### `train_all_models(X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, ModelResult]`

Trains all supported models and compares performance.

**Returns**:
- `Dict[str, ModelResult]`: Results for all trained models

##### `get_best_model() -> Tuple[str, ModelResult]`

Returns the best performing model based on cross-validation scores.

**Example**:
```python
trainer = ModelTrainer(cv_folds=5, n_jobs=-1)

# Train all models
results = trainer.train_all_models(X_train, y_train)

# Get best model
best_name, best_result = trainer.get_best_model()
print(f"Best model: {best_name} (CV Score: {best_result.cv_mean:.4f})")

# Train single model
from sklearn.ensemble import RandomForestRegressor
rf_result = trainer.train_single_model(
    name='custom_rf',
    model=RandomForestRegressor(random_state=42),
    param_grid={'n_estimators': [50, 100], 'max_depth': [5, 10]},
    X_train=X_train,
    y_train=y_train
)
```

---

## Model Evaluation

### `evaluation.evaluator`

#### `ModelEvaluator`

**Purpose**: Comprehensive model evaluation with metrics and visualizations.

**Class Definition**:
```python
class ModelEvaluator:
    def __init__(self, feature_names: Optional[List[str]] = None)
```

**Key Methods**:

##### `calculate_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]`

Calculates comprehensive regression metrics.

**Parameters**:
- `y_true` (np.ndarray): True target values
- `y_pred` (np.ndarray): Predicted target values

**Returns**:
- `Dict[str, float]`: Dictionary with metrics:
  - `RMSE`: Root Mean Square Error
  - `MAE`: Mean Absolute Error  
  - `R2`: R-squared coefficient
  - `MAPE`: Mean Absolute Percentage Error
  - `Max_Error`: Maximum absolute error
  - `Mean_Error`: Mean error (bias)

##### `plot_predictions(y_true: np.ndarray, y_pred: np.ndarray, title: str = "Predictions vs Actual", save_path: Optional[str] = None) -> plt.Figure`

Creates scatter plot of predictions vs actual values.

##### `plot_residuals(y_true: np.ndarray, y_pred: np.ndarray, title: str = "Residual Plot", save_path: Optional[str] = None) -> plt.Figure`

Creates residual plot for error analysis.

##### `generate_evaluation_report(y_true: np.ndarray, y_pred: np.ndarray, model_name: str = "Model") -> Dict[str, Any]`

Generates comprehensive evaluation report.

**Example**:
```python
evaluator = ModelEvaluator(feature_names=feature_names)

# Calculate metrics
metrics = evaluator.calculate_regression_metrics(y_test, y_pred)
print("RMSE:", metrics['RMSE'])
print("R²:", metrics['R2'])

# Generate plots
fig1 = evaluator.plot_predictions(y_test, y_pred, save_path='predictions.png')
fig2 = evaluator.plot_residuals(y_test, y_pred, save_path='residuals.png')

# Full evaluation report
report = evaluator.generate_evaluation_report(y_test, y_pred, "Random Forest")
```

### `evaluation.feature_analyzer`

#### `FeatureAnalyzer`

**Purpose**: Analyzes feature importance and provides model interpretability.

**Class Definition**:
```python
class FeatureAnalyzer:
    def __init__(self, random_state: int = 42)
```

**Key Methods**:

##### `analyze_feature_importance(model: Any, feature_names: List[str], X_test: np.ndarray, y_test: np.ndarray, method: str = 'builtin') -> pd.DataFrame`

Analyzes feature importance using various methods.

**Parameters**:
- `model` (Any): Trained model
- `feature_names` (List[str]): Feature names
- `X_test` (np.ndarray): Test features for permutation importance
- `y_test` (np.ndarray): Test targets
- `method` (str): Importance method ('builtin', 'permutation', 'both')

**Returns**:
- `pd.DataFrame`: Feature importance rankings

##### `plot_feature_importance(importance_df: pd.DataFrame, top_n: int = 20, save_path: Optional[str] = None) -> plt.Figure`

Creates feature importance visualization.

**Example**:
```python
analyzer = FeatureAnalyzer()

# Analyze feature importance
importance_df = analyzer.analyze_feature_importance(
    model=trained_model,
    feature_names=feature_names,
    X_test=X_test,
    y_test=y_test,
    method='both'
)

# Plot importance
fig = analyzer.plot_feature_importance(importance_df, top_n=15)
```

---

## Model Persistence

### `models.persistence`

#### `ModelPersistence`

**Purpose**: Handles model and pipeline saving/loading with metadata management.

**Class Definition**:
```python
class ModelPersistence:
    def __init__(self, 
                 base_path: str = "models/",
                 compression: bool = True,
                 include_metadata: bool = True)
```

**Key Methods**:

##### `save_model(model_info: Dict[str, Any], filepath: str) -> bool`

Saves model with comprehensive metadata.

**Parameters**:
- `model_info` (Dict): Model information including:
  - `model`: The trained model
  - `feature_names`: List of feature names
  - `target_name`: Target variable name
  - `preprocessing_steps`: List of preprocessing steps
  - `metrics`: Performance metrics
- `filepath` (str): Save path

**Returns**:
- `bool`: Success status

##### `load_model(filepath: str) -> Optional[Dict[str, Any]]`

Loads model with metadata.

##### `save_preprocessing_pipeline(pipeline_info: Dict[str, Any], filepath: str) -> bool`

Saves preprocessing pipeline.

##### `load_preprocessing_pipeline(filepath: str) -> Optional[Dict[str, Any]]`

Loads preprocessing pipeline.

**Example**:
```python
persistence = ModelPersistence(base_path="models/")

# Save model
model_info = {
    'model': trained_model,
    'feature_names': feature_names,
    'target_name': 'total_amount',
    'preprocessing_steps': ['numeric_scaling', 'categorical_encoding'],
    'metrics': {'RMSE': 50000, 'R2': 0.85}
}

success = persistence.save_model(model_info, "best_model.joblib")

# Load model
loaded_info = persistence.load_model("best_model.joblib")
if loaded_info:
    model = loaded_info['model']
    features = loaded_info['feature_names']
```

#### `ModelPredictor`

**Purpose**: Production-ready prediction interface with preprocessing integration.

**Class Definition**:
```python
class ModelPredictor:
    def __init__(self, model_path: str, preprocessing_path: Optional[str] = None)
```

**Key Methods**:

##### `predict(input_data: Union[pd.DataFrame, Dict, np.ndarray]) -> np.ndarray`

Makes predictions on new data with automatic preprocessing.

##### `predict_single(input_dict: Dict[str, Any]) -> float`

Makes prediction for single instance.

##### `predict_with_confidence(input_data: Union[pd.DataFrame, Dict, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]`

Makes predictions with confidence intervals (for supported models).

**Example**:
```python
predictor = ModelPredictor(
    model_path="models/best_model.joblib",
    preprocessing_path="models/preprocessing_pipeline.joblib"
)

# Single prediction
prediction = predictor.predict_single({
    'carpet_area': 1200,
    'bathroom': 2,
    'furnishing': 'Semi-Furnished'
})

# Batch predictions
predictions = predictor.predict(new_houses_df)
```

---

## Experiment Tracking

### `experiment_tracking.enhanced_trainer`

#### `EnhancedModelTrainer`

**Purpose**: Model trainer with Weights & Biases integration for experiment tracking.

**Class Definition**:
```python
class EnhancedModelTrainer(ModelTrainer):
    def __init__(self,
                 project_name: str = "house-price-prediction",
                 experiment_name: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 **trainer_kwargs)
```

**Key Methods**:

##### `train_all_models_with_tracking(X_train: np.ndarray, y_train: np.ndarray, X_val: Optional[np.ndarray] = None, y_val: Optional[np.ndarray] = None) -> Dict[str, ModelResult]`

Trains models with comprehensive experiment tracking.

##### `log_dataset_info(dataset_info: Dict[str, Any])`

Logs dataset information to W&B.

##### `log_preprocessing_info(preprocessing_info: Dict[str, Any])`

Logs preprocessing configuration.

**Example**:
```python
enhanced_trainer = EnhancedModelTrainer(
    project_name="house-price-prediction",
    experiment_name="baseline-experiment",
    tags=["baseline", "random-forest"],
    cv_folds=5
)

# Train with tracking
results = enhanced_trainer.train_all_models_with_tracking(
    X_train, y_train, X_val, y_val
)

# Log additional info
enhanced_trainer.log_dataset_info({
    'train_size': len(X_train),
    'n_features': X_train.shape[1],
    'target_mean': np.mean(y_train)
})
```

---

## Error Handling

All components implement comprehensive error handling:

### Common Exceptions

- **`DataValidationError`**: Raised when data validation fails
- **`PreprocessingError`**: Raised during preprocessing failures
- **`ModelTrainingError`**: Raised when model training fails
- **`PersistenceError`**: Raised during save/load operations

### Error Handling Pattern

```python
try:
    df, report = load_house_price_data('data.csv')
    preprocessor = UnifiedPreprocessor()
    preprocessor.fit(df)
    # ... continue processing
except DataValidationError as e:
    logger.error(f"Data validation failed: {e}")
    # Handle validation error
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle generic error
```

---

## Configuration

### Environment Variables

- `WANDB_PROJECT`: W&B project name
- `WANDB_ENTITY`: W&B entity/username
- `DATA_PATH`: Default data file path
- `MODEL_OUTPUT_PATH`: Default model output directory

### Logging Configuration

All modules use Python's logging framework. Configure logging level:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

---

This API documentation provides comprehensive coverage of all major components in the House Price Prediction ML Pipeline. For additional examples and usage patterns, refer to the notebooks and test files in the repository.