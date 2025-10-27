"""
Numeric feature preprocessing utilities.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
import logging
from typing import List, Optional, Union

logger = logging.getLogger(__name__)


class NumericPreprocessor(BaseEstimator, TransformerMixin):
    """
    Custom transformer for numeric feature preprocessing.
    
    Handles missing value imputation and feature scaling for numeric columns.
    """
    
    def __init__(self, 
                 imputation_strategy: str = 'median',
                 scaling: bool = True,
                 handle_outliers: bool = False,
                 outlier_method: str = 'iqr',
                 outlier_threshold: float = 3.0):
        """
        Initialize numeric preprocessor.
        
        Args:
            imputation_strategy: Strategy for imputing missing values ('median', 'mean', 'constant')
            scaling: Whether to apply StandardScaler
            handle_outliers: Whether to clip outliers
            outlier_method: Method for outlier detection ('iqr', 'zscore')
            outlier_threshold: Threshold for outlier detection
        """
        self.imputation_strategy = imputation_strategy
        self.scaling = scaling
        self.handle_outliers = handle_outliers
        self.outlier_method = outlier_method
        self.outlier_threshold = outlier_threshold
        
        # Will be set during fit
        self.imputer = None
        self.scaler = None
        self.outlier_bounds = {}
        self.feature_names = []
        self.n_features_in_ = None
        
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
        
        logger.info(f"Fitting numeric preprocessor on {len(self.feature_names)} features")
        
        # Fit imputer
        self._fit_imputer(X)
        
        # Apply imputation for outlier detection and scaling
        X_imputed = pd.DataFrame(
            self.imputer.transform(X),
            columns=self.feature_names,
            index=X.index
        )
        
        # Fit outlier bounds
        if self.handle_outliers:
            self._fit_outlier_bounds(X_imputed)
        
        # Fit scaler
        if self.scaling:
            self._fit_scaler(X_imputed)
        
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
        X_transformed = pd.DataFrame(
            self.imputer.transform(X),
            columns=self.feature_names,
            index=X.index
        )
        
        # Handle outliers
        if self.handle_outliers:
            X_transformed = self._clip_outliers(X_transformed)
        
        # Apply scaling
        if self.scaling:
            X_transformed = pd.DataFrame(
                self.scaler.transform(X_transformed),
                columns=self.feature_names,
                index=X.index
            )
        
        return X_transformed.values
    
    def _fit_imputer(self, X: pd.DataFrame):
        """Fit the imputation strategy."""
        if self.imputation_strategy == 'constant':
            self.imputer = SimpleImputer(strategy='constant', fill_value=0)
        else:
            self.imputer = SimpleImputer(strategy=self.imputation_strategy)
        
        self.imputer.fit(X)
        
        # Log imputation statistics
        for i, feature in enumerate(self.feature_names):
            missing_count = X[feature].isnull().sum()
            if missing_count > 0:
                fill_value = self.imputer.statistics_[i] if self.imputation_strategy != 'constant' else 0
                logger.info(f"Feature '{feature}': {missing_count} missing values, "
                          f"imputing with {self.imputation_strategy} = {fill_value:.2f}")
    
    def _fit_outlier_bounds(self, X: pd.DataFrame):
        """Fit outlier detection bounds."""
        logger.info(f"Fitting outlier bounds using {self.outlier_method} method")
        
        for feature in self.feature_names:
            if self.outlier_method == 'iqr':
                Q1 = X[feature].quantile(0.25)
                Q3 = X[feature].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - self.outlier_threshold * IQR
                upper_bound = Q3 + self.outlier_threshold * IQR
            elif self.outlier_method == 'zscore':
                mean = X[feature].mean()
                std = X[feature].std()
                lower_bound = mean - self.outlier_threshold * std
                upper_bound = mean + self.outlier_threshold * std
            else:
                raise ValueError(f"Unknown outlier method: {self.outlier_method}")
            
            self.outlier_bounds[feature] = (lower_bound, upper_bound)
            
            # Log outlier statistics
            outliers = ((X[feature] < lower_bound) | (X[feature] > upper_bound)).sum()
            if outliers > 0:
                logger.info(f"Feature '{feature}': {outliers} outliers detected, "
                          f"bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
    
    def _fit_scaler(self, X: pd.DataFrame):
        """Fit the StandardScaler."""
        self.scaler = StandardScaler()
        self.scaler.fit(X)
        
        logger.info("Fitted StandardScaler for feature normalization")
    
    def _clip_outliers(self, X: pd.DataFrame) -> pd.DataFrame:
        """Clip outliers using fitted bounds."""
        X_clipped = X.copy()
        
        for feature, (lower_bound, upper_bound) in self.outlier_bounds.items():
            X_clipped[feature] = X_clipped[feature].clip(lower=lower_bound, upper=upper_bound)
        
        return X_clipped
    
    def get_feature_names_out(self, input_features=None) -> List[str]:
        """Get output feature names."""
        if input_features is None:
            return self.feature_names
        return list(input_features)


def create_numeric_pipeline(
    imputation_strategy: str = 'median',
    scaling: bool = True,
    handle_outliers: bool = False
) -> Pipeline:
    """
    Create a scikit-learn pipeline for numeric preprocessing.
    
    Args:
        imputation_strategy: Strategy for missing value imputation
        scaling: Whether to apply standard scaling
        handle_outliers: Whether to handle outliers
        
    Returns:
        sklearn Pipeline object
    """
    preprocessor = NumericPreprocessor(
        imputation_strategy=imputation_strategy,
        scaling=scaling,
        handle_outliers=handle_outliers
    )
    
    pipeline = Pipeline([
        ('numeric_preprocessor', preprocessor)
    ])
    
    return pipeline


def analyze_numeric_features(df: pd.DataFrame, features: List[str]) -> dict:
    """
    Analyze numeric features for preprocessing insights.
    
    Args:
        df: Input DataFrame
        features: List of numeric feature names
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'summary_stats': {},
        'missing_values': {},
        'outliers': {},
        'distributions': {}
    }
    
    for feature in features:
        if feature not in df.columns:
            logger.warning(f"Feature '{feature}' not found in DataFrame")
            continue
        
        series = df[feature]
        
        # Summary statistics
        analysis['summary_stats'][feature] = {
            'count': series.count(),
            'mean': series.mean() if series.dtype in ['int64', 'float64'] else None,
            'std': series.std() if series.dtype in ['int64', 'float64'] else None,
            'min': series.min() if series.dtype in ['int64', 'float64'] else None,
            'max': series.max() if series.dtype in ['int64', 'float64'] else None,
            'median': series.median() if series.dtype in ['int64', 'float64'] else None,
        }
        
        # Missing values
        missing_count = series.isnull().sum()
        analysis['missing_values'][feature] = {
            'count': missing_count,
            'percentage': missing_count / len(series) * 100
        }
        
        # Outlier detection (IQR method)
        if series.dtype in ['int64', 'float64'] and series.count() > 0:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = ((series < lower_bound) | (series > upper_bound)).sum()
            
            analysis['outliers'][feature] = {
                'count': outliers,
                'percentage': outliers / len(series) * 100,
                'bounds': (lower_bound, upper_bound)
            }
        
        # Distribution analysis
        if series.dtype in ['int64', 'float64'] and series.count() > 0:
            from scipy import stats
            try:
                skewness = stats.skew(series.dropna())
                kurtosis = stats.kurtosis(series.dropna())
                analysis['distributions'][feature] = {
                    'skewness': skewness,
                    'kurtosis': kurtosis,
                    'is_normal': abs(skewness) < 1 and abs(kurtosis) < 3
                }
            except ImportError:
                # scipy not available
                analysis['distributions'][feature] = {
                    'skewness': None,
                    'kurtosis': None,
                    'is_normal': None
                }
    
    return analysis


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    np.random.seed(42)
    data = {
        'area': np.random.normal(1000, 200, 100),
        'price': np.random.normal(500000, 100000, 100),
        'rooms': np.random.poisson(3, 100)
    }
    
    # Add some missing values and outliers
    data['area'][::10] = np.nan
    data['price'][0] = 2000000  # outlier
    
    df = pd.DataFrame(data)
    
    # Create and test preprocessor
    preprocessor = create_numeric_pipeline(handle_outliers=True)
    X_transformed = preprocessor.fit_transform(df)
    
    print("Original shape:", df.shape)
    print("Transformed shape:", X_transformed.shape)
    print("Transformed data sample:")
    print(X_transformed[:5])