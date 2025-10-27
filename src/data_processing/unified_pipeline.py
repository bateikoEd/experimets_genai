"""
Unified preprocessing pipeline combining numeric, categorical, and text features.
"""

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
import logging
from typing import Dict, List, Optional, Union, Any
import os

from .numeric_preprocessing import NumericPreprocessor
from .categorical_preprocessing import CategoricalPreprocessor
from .text_preprocessing import TextPreprocessor

logger = logging.getLogger(__name__)


class UnifiedPreprocessor(BaseEstimator, TransformerMixin):
    """
    Unified preprocessing pipeline for house price prediction features.
    
    Automatically handles numeric, categorical, and text features using
    appropriate preprocessing strategies.
    """
    
    def __init__(self,
                 target_col: str = 'total_amount',
                 numeric_imputation: str = 'median',
                 numeric_scaling: bool = True,
                 categorical_rare_threshold: float = 0.01,
                 categorical_max_categories: Optional[int] = None,
                 text_max_features: int = 5000,
                 text_use_ner: bool = True,
                 auto_detect_types: bool = True):
        """
        Initialize unified preprocessor.
        
        Args:
            target_col: Name of target variable (excluded from preprocessing)
            numeric_imputation: Strategy for numeric missing values
            numeric_scaling: Whether to scale numeric features
            categorical_rare_threshold: Threshold for rare category grouping
            categorical_max_categories: Max categories per categorical feature
            text_max_features: Maximum TF-IDF features for text
            text_use_ner: Whether to extract NER features from text
            auto_detect_types: Whether to automatically detect feature types
        """
        self.target_col = target_col
        self.numeric_imputation = numeric_imputation
        self.numeric_scaling = numeric_scaling
        self.categorical_rare_threshold = categorical_rare_threshold
        self.categorical_max_categories = categorical_max_categories
        self.text_max_features = text_max_features
        self.text_use_ner = text_use_ner
        self.auto_detect_types = auto_detect_types
        
        # Will be set during fit
        self.feature_types = {}
        self.column_transformer = None
        self.feature_names_out = []
        
    def fit(self, X: pd.DataFrame, y=None):
        """
        Fit the unified preprocessor.
        
        Args:
            X: Input DataFrame with all features
            y: Target values (ignored)
            
        Returns:
            self
        """
        logger.info(f"Fitting unified preprocessor on data shape: {X.shape}")
        
        # Remove target column if present
        X_features = X.drop(columns=[self.target_col], errors='ignore')
        
        # Detect feature types
        if self.auto_detect_types:
            self.feature_types = self._detect_feature_types(X_features)
        else:
            # Use all features as numeric by default if not auto-detecting
            self.feature_types = {
                'numeric': list(X_features.columns),
                'categorical': [],
                'text': []
            }
        
        # Log feature type distribution
        self._log_feature_distribution()
        
        # Create preprocessing steps
        transformers = self._create_transformers()
        
        # Create ColumnTransformer
        self.column_transformer = ColumnTransformer(
            transformers=transformers,
            remainder='drop',  # Drop any unspecified columns
            sparse_threshold=0  # Return dense array
        )
        
        # Fit the transformer
        self.column_transformer.fit(X_features)
        
        # Store output feature names
        self._set_output_feature_names()
        
        logger.info(f"Fitted preprocessor. Output features: {len(self.feature_names_out)}")
        
        return self
    
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transform input data using fitted preprocessor.
        
        Args:
            X: Input DataFrame
            
        Returns:
            Transformed feature matrix
        """
        # Remove target column if present
        X_features = X.drop(columns=[self.target_col], errors='ignore')
        
        # Transform using fitted column transformer
        X_transformed = self.column_transformer.transform(X_features)
        
        logger.info(f"Transformed data shape: {X_transformed.shape}")
        
        return X_transformed
    
    def fit_transform(self, X: pd.DataFrame, y=None) -> np.ndarray:
        """Fit and transform in one step."""
        return self.fit(X, y).transform(X)
    
    def _detect_feature_types(self, X: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Automatically detect feature types based on data characteristics.
        
        Args:
            X: Input DataFrame
            
        Returns:
            Dictionary mapping feature types to column names
        """
        feature_types = {
            'numeric': [],
            'categorical': [],
            'text': []
        }
        
        for col in X.columns:
            if col == self.target_col:
                continue
                
            series = X[col]
            
            # Check if numeric
            if pd.api.types.is_numeric_dtype(series):
                feature_types['numeric'].append(col)
            
            # Check if categorical (string/object with limited unique values)
            elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
                unique_ratio = series.nunique() / len(series)
                avg_length = series.astype(str).str.len().mean()
                
                # Heuristics for categorical vs text
                if unique_ratio < 0.1 or (unique_ratio < 0.5 and avg_length < 50):
                    feature_types['categorical'].append(col)
                else:
                    feature_types['text'].append(col)
            
            # Default to categorical for other types
            else:
                feature_types['categorical'].append(col)
        
        return feature_types
    
    def _log_feature_distribution(self):
        """Log the distribution of feature types."""
        logger.info("Feature type distribution:")
        for ftype, features in self.feature_types.items():
            logger.info(f"  {ftype}: {len(features)} features")
            if features:
                logger.info(f"    {features[:5]}{'...' if len(features) > 5 else ''}")
    
    def _create_transformers(self) -> List:
        """Create preprocessing transformers for each feature type."""
        transformers = []
        
        # Numeric features
        if self.feature_types['numeric']:
            numeric_preprocessor = NumericPreprocessor(
                imputation_strategy=self.numeric_imputation,
                scaling=self.numeric_scaling,
                handle_outliers=False  # Keep outliers for now
            )
            
            transformers.append((
                'numeric',
                numeric_preprocessor,
                self.feature_types['numeric']
            ))
        
        # Categorical features
        if self.feature_types['categorical']:
            categorical_preprocessor = CategoricalPreprocessor(
                rare_threshold=self.categorical_rare_threshold,
                max_categories=self.categorical_max_categories,
                handle_unknown='ignore'
            )
            
            transformers.append((
                'categorical',
                categorical_preprocessor,
                self.feature_types['categorical']
            ))
        
        # Text features
        if self.feature_types['text']:
            text_preprocessor = TextPreprocessor(
                max_features=self.text_max_features,
                use_ner=self.text_use_ner,
                clean_text=True
            )
            
            transformers.append((
                'text',
                text_preprocessor,
                self.feature_types['text']
            ))
        
        return transformers
    
    def _set_output_feature_names(self):
        """Set output feature names from fitted transformers."""
        self.feature_names_out = []
        
        # Get feature names from each transformer
        for name, transformer, columns in self.column_transformer.transformers_:
            if name == 'remainder':
                continue
                
            if hasattr(transformer, 'get_feature_names_out'):
                feature_names = transformer.get_feature_names_out(columns)
                # Add prefix to avoid naming conflicts
                prefixed_names = [f"{name}_{fname}" for fname in feature_names]
                self.feature_names_out.extend(prefixed_names)
            else:
                # Fallback to column names
                self.feature_names_out.extend([f"{name}_{col}" for col in columns])
    
    def get_feature_names_out(self, input_features=None) -> List[str]:
        """Get output feature names."""
        return self.feature_names_out
    
    def get_feature_importance_mapping(self) -> Dict[str, str]:
        """
        Create mapping from output feature names to original features.
        
        Returns:
            Dictionary mapping output features to original feature names
        """
        mapping = {}
        
        for name, transformer, columns in self.column_transformer.transformers_:
            if name == 'remainder':
                continue
            
            if hasattr(transformer, 'get_feature_names_out'):
                output_names = transformer.get_feature_names_out(columns)
                
                for i, output_name in enumerate(output_names):
                    prefixed_name = f"{name}_{output_name}"
                    
                    # Try to map back to original column
                    if name == 'numeric':
                        original_col = columns[i] if i < len(columns) else 'unknown'
                    elif name == 'categorical':
                        # OneHot encoding creates multiple features per column
                        original_col = output_name.split('_')[0] if '_' in output_name else 'unknown'
                    elif name == 'text':
                        # TF-IDF features map to combined text
                        original_col = 'text_combined'
                    else:
                        original_col = 'unknown'
                    
                    mapping[prefixed_name] = original_col
        
        return mapping


def create_full_pipeline(
    target_col: str = 'total_amount',
    config: Optional[Dict[str, Any]] = None
) -> Pipeline:
    """
    Create a complete preprocessing pipeline.
    
    Args:
        target_col: Name of target variable
        config: Configuration dictionary for preprocessing parameters
        
    Returns:
        sklearn Pipeline with unified preprocessing
    """
    if config is None:
        config = {}
    
    # Get configuration with defaults
    preprocessor_config = {
        'target_col': target_col,
        'numeric_imputation': config.get('numeric_imputation', 'median'),
        'numeric_scaling': config.get('numeric_scaling', True),
        'categorical_rare_threshold': config.get('categorical_rare_threshold', 0.01),
        'text_max_features': config.get('text_max_features', 5000),
        'text_use_ner': config.get('text_use_ner', True),
    }
    
    preprocessor = UnifiedPreprocessor(**preprocessor_config)
    
    pipeline = Pipeline([
        ('preprocessor', preprocessor)
    ])
    
    return pipeline


def load_preprocessing_config() -> Dict[str, Any]:
    """
    Load preprocessing configuration from environment variables.
    
    Returns:
        Configuration dictionary
    """
    config = {
        'target_col': os.getenv('TARGET_COL', 'total_amount'),
        'numeric_imputation': os.getenv('NUMERIC_IMPUTATION', 'median'),
        'numeric_scaling': os.getenv('NUMERIC_SCALING', 'True').lower() == 'true',
        'categorical_rare_threshold': float(os.getenv('RARE_CATEGORY_THRESHOLD', '0.01')),
        'text_max_features': int(os.getenv('MAX_TFIDF_FEATURES', '5000')),
        'text_use_ner': os.getenv('USE_NER_FEATURES', 'True').lower() == 'true',
    }
    
    return config


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample mixed-type data
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        # Numeric features
        'carpet_area': np.random.normal(1000, 200, n_samples),
        'bathroom': np.random.poisson(2, n_samples),
        'price_per_sqft': np.random.normal(5000, 1000, n_samples),
        
        # Categorical features  
        'furnishing': np.random.choice(['Furnished', 'Semi-Furnished', 'Unfurnished'], n_samples),
        'property_status': np.random.choice(['Ready to Move', 'Under Construction'], n_samples),
        
        # Text features
        'description': [f"Beautiful {np.random.choice(['2BHK', '3BHK'])} apartment" for _ in range(n_samples)],
        'location': [f"{np.random.choice(['Bandra', 'Andheri', 'Powai'])}, Mumbai" for _ in range(n_samples)],
        
        # Target
        'total_amount': np.random.normal(5000000, 1000000, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Add some missing values
    df.loc[::10, 'carpet_area'] = np.nan
    df.loc[::15, 'furnishing'] = np.nan
    df.loc[::20, 'description'] = np.nan
    
    print("Original data shape:", df.shape)
    print("Original columns:", list(df.columns))
    
    # Create and test pipeline
    config = load_preprocessing_config()
    pipeline = create_full_pipeline(config=config)
    
    X_transformed = pipeline.fit_transform(df)
    
    print("Transformed data shape:", X_transformed.shape)
    
    # Get feature names
    preprocessor = pipeline.named_steps['preprocessor']
    feature_names = preprocessor.get_feature_names_out()
    print(f"Number of output features: {len(feature_names)}")
    print(f"Sample feature names: {feature_names[:10]}")