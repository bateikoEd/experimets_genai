"""
Categorical feature preprocessing utilities.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
import logging
from typing import List, Optional, Union, Dict

logger = logging.getLogger(__name__)


class CategoricalPreprocessor(BaseEstimator, TransformerMixin):
    """
    Custom transformer for categorical feature preprocessing.
    
    Handles missing values, rare categories, and one-hot encoding.
    """
    
    def __init__(self,
                 rare_threshold: float = 0.01,
                 rare_category_name: str = 'Other',
                 missing_strategy: str = 'most_frequent',
                 handle_unknown: str = 'ignore',
                 max_categories: Optional[int] = None):
        """
        Initialize categorical preprocessor.
        
        Args:
            rare_threshold: Threshold for rare category grouping (as fraction of total)
            rare_category_name: Name for grouped rare categories
            missing_strategy: Strategy for missing value imputation
            handle_unknown: How to handle unknown categories during transform
            max_categories: Maximum number of categories per feature (None for no limit)
        """
        self.rare_threshold = rare_threshold
        self.rare_category_name = rare_category_name
        self.missing_strategy = missing_strategy
        self.handle_unknown = handle_unknown
        self.max_categories = max_categories
        
        # Will be set during fit
        self.imputer = None
        self.encoder = None
        self.rare_category_maps = {}
        self.feature_names = []
        self.n_features_in_ = None
        self.output_feature_names = []
        
    def fit(self, X: Union[pd.DataFrame, np.ndarray], y=None):
        """
        Fit the preprocessor to training data.
        
        Args:
            X: Training data
            y: Target values (ignored)
            
        Returns:
            self
        """
        # Convert to DataFrame if needed
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(X.shape[1])])
        
        self.feature_names = list(X.columns)
        self.n_features_in_ = X.shape[1]
        
        logger.info(f"Fitting categorical preprocessor on {len(self.feature_names)} features")
        
        # Fit missing value imputer
        self._fit_imputer(X)
        
        # Apply imputation
        X_imputed = pd.DataFrame(
            self.imputer.transform(X),
            columns=self.feature_names,
            index=X.index
        )
        
        # Handle rare categories
        X_processed = self._fit_rare_categories(X_imputed)
        
        # Fit one-hot encoder
        self._fit_encoder(X_processed)
        
        return self
    
    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """
        Transform input data using fitted preprocessor.
        
        Args:
            X: Input data
            
        Returns:
            Transformed data as numpy array
        """
        # Convert to DataFrame if needed
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X, columns=self.feature_names)
        
        # Validate input
        if X.shape[1] != self.n_features_in_:
            raise ValueError(f"Expected {self.n_features_in_} features, got {X.shape[1]}")
        
        # Apply imputation
        X_imputed = pd.DataFrame(
            self.imputer.transform(X),
            columns=self.feature_names,
            index=X.index
        )
        
        # Handle rare categories
        X_processed = self._apply_rare_categories(X_imputed)
        
        # Apply one-hot encoding
        X_encoded = self.encoder.transform(X_processed)
        
        return X_encoded
    
    def _fit_imputer(self, X: pd.DataFrame):
        """Fit the missing value imputer."""
        self.imputer = SimpleImputer(strategy=self.missing_strategy)
        self.imputer.fit(X)
        
        # Log imputation statistics
        for i, feature in enumerate(self.feature_names):
            missing_count = X[feature].isnull().sum()
            if missing_count > 0:
                fill_value = self.imputer.statistics_[i]
                logger.info(f"Feature '{feature}': {missing_count} missing values, "
                          f"imputing with '{fill_value}'")
    
    def _fit_rare_categories(self, X: pd.DataFrame) -> pd.DataFrame:
        """Identify and map rare categories."""
        X_processed = X.copy()
        
        for feature in self.feature_names:
            # Calculate value counts
            value_counts = X[feature].value_counts()
            total_count = len(X)
            
            # Identify rare categories
            rare_categories = []
            for category, count in value_counts.items():
                if count / total_count < self.rare_threshold:
                    rare_categories.append(category)
            
            # Apply max_categories limit if specified
            if self.max_categories and len(value_counts) > self.max_categories:
                # Keep top N-1 categories, group rest as rare
                top_categories = value_counts.head(self.max_categories - 1).index.tolist()
                rare_categories = [cat for cat in value_counts.index if cat not in top_categories]
            
            # Store mapping for transform
            self.rare_category_maps[feature] = set(rare_categories)
            
            # Apply rare category mapping
            if rare_categories:
                X_processed.loc[X_processed[feature].isin(rare_categories), feature] = self.rare_category_name
                logger.info(f"Feature '{feature}': Grouped {len(rare_categories)} rare categories "
                          f"as '{self.rare_category_name}'")
            
            # Log final category counts
            final_categories = X_processed[feature].nunique()
            logger.info(f"Feature '{feature}': {final_categories} final categories")
        
        return X_processed
    
    def _apply_rare_categories(self, X: pd.DataFrame) -> pd.DataFrame:
        """Apply rare category mapping to new data."""
        X_processed = X.copy()
        
        for feature in self.feature_names:
            rare_categories = self.rare_category_maps.get(feature, set())
            if rare_categories:
                mask = X_processed[feature].isin(rare_categories)
                X_processed.loc[mask, feature] = self.rare_category_name
        
        return X_processed
    
    def _fit_encoder(self, X: pd.DataFrame):
        """Fit the one-hot encoder."""
        self.encoder = OneHotEncoder(
            handle_unknown=self.handle_unknown,
            sparse_output=True,  # Use sparse matrix for memory efficiency
            drop='first' if len(self.feature_names) > 1 else None  # Drop first to avoid multicollinearity
        )
        
        self.encoder.fit(X)
        
        # Store output feature names
        self.output_feature_names = self.encoder.get_feature_names_out(self.feature_names)
        
        logger.info(f"One-hot encoder fitted. Output features: {len(self.output_feature_names)}")
        
        # Log encoding details
        for i, feature in enumerate(self.feature_names):
            categories = self.encoder.categories_[i]
            logger.info(f"Feature '{feature}': {len(categories)} categories encoded")
    
    def get_feature_names_out(self, input_features=None) -> List[str]:
        """Get output feature names after transformation."""
        return list(self.output_feature_names)


class RareCategoryHandler(BaseEstimator, TransformerMixin):
    """
    Standalone transformer for handling rare categories.
    
    Can be used independently or as part of a pipeline.
    """
    
    def __init__(self, threshold: float = 0.01, rare_name: str = 'Other'):
        """
        Initialize rare category handler.
        
        Args:
            threshold: Frequency threshold for rare categories
            rare_name: Name to assign to rare categories
        """
        self.threshold = threshold
        self.rare_name = rare_name
        self.category_maps = {}
        
    def fit(self, X: Union[pd.DataFrame, pd.Series], y=None):
        """Fit the rare category handler."""
        if isinstance(X, pd.Series):
            X = X.to_frame()
        
        self.category_maps = {}
        
        for column in X.columns:
            value_counts = X[column].value_counts()
            total_count = len(X)
            
            rare_categories = set()
            for category, count in value_counts.items():
                if count / total_count < self.threshold:
                    rare_categories.add(category)
            
            self.category_maps[column] = rare_categories
        
        return self
    
    def transform(self, X: Union[pd.DataFrame, pd.Series]) -> Union[pd.DataFrame, pd.Series]:
        """Transform data by replacing rare categories."""
        if isinstance(X, pd.Series):
            X = X.to_frame()
            single_series = True
        else:
            single_series = False
        
        X_transformed = X.copy()
        
        for column in X.columns:
            rare_categories = self.category_maps.get(column, set())
            if rare_categories:
                mask = X_transformed[column].isin(rare_categories)
                X_transformed.loc[mask, column] = self.rare_name
        
        return X_transformed.iloc[:, 0] if single_series else X_transformed


def create_categorical_pipeline(
    rare_threshold: float = 0.01,
    handle_unknown: str = 'ignore',
    max_categories: Optional[int] = None
) -> Pipeline:
    """
    Create a scikit-learn pipeline for categorical preprocessing.
    
    Args:
        rare_threshold: Threshold for rare category grouping
        handle_unknown: How to handle unknown categories
        max_categories: Maximum categories per feature
        
    Returns:
        sklearn Pipeline object
    """
    preprocessor = CategoricalPreprocessor(
        rare_threshold=rare_threshold,
        handle_unknown=handle_unknown,
        max_categories=max_categories
    )
    
    pipeline = Pipeline([
        ('categorical_preprocessor', preprocessor)
    ])
    
    return pipeline


def analyze_categorical_features(df: pd.DataFrame, features: List[str]) -> Dict:
    """
    Analyze categorical features for preprocessing insights.
    
    Args:
        df: Input DataFrame
        features: List of categorical feature names
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'cardinality': {},
        'missing_values': {},
        'rare_categories': {},
        'most_frequent': {},
    }
    
    for feature in features:
        if feature not in df.columns:
            logger.warning(f"Feature '{feature}' not found in DataFrame")
            continue
        
        series = df[feature]
        
        # Cardinality
        unique_count = series.nunique()
        analysis['cardinality'][feature] = {
            'unique_values': unique_count,
            'cardinality_ratio': unique_count / len(series)
        }
        
        # Missing values
        missing_count = series.isnull().sum()
        analysis['missing_values'][feature] = {
            'count': missing_count,
            'percentage': missing_count / len(series) * 100
        }
        
        # Value frequency analysis
        value_counts = series.value_counts()
        total_count = len(series)
        
        # Rare categories (< 1% frequency)
        rare_categories = []
        for category, count in value_counts.items():
            if count / total_count < 0.01:
                rare_categories.append(category)
        
        analysis['rare_categories'][feature] = {
            'count': len(rare_categories),
            'percentage': len(rare_categories) / unique_count * 100 if unique_count > 0 else 0,
            'categories': rare_categories[:10]  # Show first 10 for brevity
        }
        
        # Most frequent categories
        top_categories = value_counts.head(5)
        analysis['most_frequent'][feature] = {
            category: {
                'count': count,
                'percentage': count / total_count * 100
            }
            for category, count in top_categories.items()
        }
    
    return analysis


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    np.random.seed(42)
    categories = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']  # Some will be rare
    weights = [0.3, 0.25, 0.15, 0.1, 0.08, 0.05, 0.03, 0.02, 0.01, 0.01]  # Last few are rare
    
    data = {
        'category1': np.random.choice(categories, size=1000, p=weights),
        'category2': np.random.choice(['X', 'Y', 'Z'], size=1000, p=[0.5, 0.3, 0.2]),
    }
    
    # Add some missing values
    data['category1'][::50] = np.nan
    
    df = pd.DataFrame(data)
    
    # Analyze features
    analysis = analyze_categorical_features(df, ['category1', 'category2'])
    print("Categorical analysis:")
    for feature, stats in analysis['rare_categories'].items():
        print(f"{feature}: {stats['count']} rare categories")
    
    # Create and test preprocessor
    preprocessor = create_categorical_pipeline(rare_threshold=0.02)
    X_transformed = preprocessor.fit_transform(df)
    
    print("Original shape:", df.shape)
    print("Transformed shape:", X_transformed.shape)
    print("Output is sparse matrix:", hasattr(X_transformed, 'toarray'))