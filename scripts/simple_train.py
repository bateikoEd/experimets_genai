#!/usr/bin/env python3
"""
Simple training script that works with the actual house prices dataset format.
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_and_prepare_data(file_path: str, target_col: str = "Amount(in rupees)") -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load and prepare the house prices dataset.
    
    Args:
        file_path: Path to CSV file
        target_col: Name of target column
        
    Returns:
        Tuple of (features_df, target_series)
    """
    logger.info(f"Loading data from: {file_path}")
    
    # Load data
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
    
    # Print column info
    logger.info(f"Columns: {list(df.columns)}")
    
    # Check if target column exists
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found in data")
        logger.info(f"Available columns: {list(df.columns)}")
        raise ValueError(f"Target column '{target_col}' not found")
    
    # Separate features and target
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Clean target variable - parse Indian price format
    def parse_indian_price(price_str):
        """Parse Indian price format like '42 Lac', '1.40 Cr' to numeric."""
        if pd.isna(price_str) or not isinstance(price_str, str):
            return np.nan
        
        price_str = price_str.strip().lower()
        
        # Skip non-price entries
        if 'call for price' in price_str or 'price on request' in price_str:
            return np.nan
        
        try:
            # Extract number part
            import re
            number_match = re.search(r'([\d.]+)', price_str)
            if not number_match:
                return np.nan
            
            number = float(number_match.group(1))
            
            # Convert based on unit
            if 'cr' in price_str or 'crore' in price_str:
                return number * 10000000  # 1 crore = 10 million
            elif 'lac' in price_str or 'lakh' in price_str:
                return number * 100000   # 1 lakh = 100 thousand
            else:
                return number  # Assume it's already in rupees
                
        except (ValueError, AttributeError):
            return np.nan
    
    # Parse prices
    y = y.apply(parse_indian_price)
    
    # Remove rows where target is NaN
    valid_mask = ~y.isna()
    X = X[valid_mask]
    y = y[valid_mask]
    
    logger.info(f"After cleaning: {len(X)} records")
    logger.info(f"Target statistics:")
    logger.info(f"  Mean: ₹{y.mean():,.0f}")
    logger.info(f"  Median: ₹{y.median():,.0f}")
    logger.info(f"  Min: ₹{y.min():,.0f}")
    logger.info(f"  Max: ₹{y.max():,.0f}")
    
    return X, y


def create_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    """
    Create preprocessing pipeline for the dataset.
    
    Args:
        X: Features DataFrame
        
    Returns:
        ColumnTransformer for preprocessing
    """
    
    # Identify numeric and categorical columns
    numeric_columns = []
    categorical_columns = []
    
    for col in X.columns:
        if X[col].dtype in ['int64', 'float64']:
            # Even numeric types might have NaN, so check if valid
            if X[col].notna().sum() > 0:
                numeric_columns.append(col)
            else:
                categorical_columns.append(col)
        else:
            # For object/string columns, check if they can be converted to numeric
            try:
                numeric_converted = pd.to_numeric(X[col], errors='coerce')
                # If at least 70% can be converted to numbers, treat as numeric
                valid_numeric_pct = numeric_converted.notna().sum() / len(X[col])
                if valid_numeric_pct > 0.7:
                    numeric_columns.append(col)
                else:
                    categorical_columns.append(col)
            except:
                categorical_columns.append(col)
    
    logger.info(f"Numeric columns ({len(numeric_columns)}): {numeric_columns}")
    logger.info(f"Categorical columns ({len(categorical_columns)}): {categorical_columns}")
    
    # Create preprocessing pipelines
    from sklearn.preprocessing import FunctionTransformer
    
    def convert_to_numeric(X):
        """Convert columns to numeric, replacing non-numeric with NaN."""
        if hasattr(X, 'columns'):
            # DataFrame
            result = X.copy()
            for col in X.columns:
                result[col] = pd.to_numeric(X[col], errors='coerce')
            return result
        else:
            # Array
            return pd.to_numeric(X.ravel(), errors='coerce').reshape(-1, 1)
    
    numeric_transformer = Pipeline(steps=[
        ('to_numeric', FunctionTransformer(convert_to_numeric, validate=False)),
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    # Combine preprocessing steps
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_columns),
            ('cat', categorical_transformer, categorical_columns)
        ]
    )
    
    return preprocessor


def train_model(X: pd.DataFrame, y: pd.Series, model_type: str = 'random_forest', 
                test_size: float = 0.2, random_state: int = 42) -> Dict:
    """
    Train a model with the specified type.
    
    Args:
        X: Features DataFrame
        y: Target Series
        model_type: Type of model to train
        test_size: Test set size
        random_state: Random seed
        
    Returns:
        Dictionary with training results
    """
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    logger.info(f"Data split: {len(X_train)} train, {len(X_test)} test")
    
    # Create preprocessor
    preprocessor = create_preprocessor(X_train)
    
    # Define models
    models = {
        'random_forest': RandomForestRegressor(n_estimators=100, random_state=random_state),
        'linear_regression': LinearRegression(),
        'ridge': Ridge(alpha=1.0),
        'lasso': Lasso(alpha=1.0),
        'decision_tree': DecisionTreeRegressor(random_state=random_state)
    }
    
    if model_type not in models:
        raise ValueError(f"Unsupported model type: {model_type}. Choose from: {list(models.keys())}")
    
    model = models[model_type]
    
    # Create full pipeline
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model)
    ])
    
    # Train model
    logger.info(f"Training {model_type} model...")
    pipeline.fit(X_train, y_train)
    
    # Make predictions
    y_pred_train = pipeline.predict(X_train)
    y_pred_test = pipeline.predict(X_test)
    
    # Calculate metrics
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    
    results = {
        'model': pipeline,
        'model_type': model_type,
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'test_mae': test_mae,
        'n_features': len(X.columns),
        'n_samples': len(X),
        'feature_names': list(X.columns)
    }
    
    logger.info(f"Training Results:")  
    logger.info(f"  Train RMSE: ₹{train_rmse:,.0f}")
    logger.info(f"  Test RMSE:  ₹{test_rmse:,.0f}")
    logger.info(f"  Train R²:   {train_r2:.4f}")
    logger.info(f"  Test R²:    {test_r2:.4f}")
    logger.info(f"  Test MAE:   ₹{test_mae:,.0f}")
    
    return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Simple House Price Model Training")
    
    parser.add_argument('--data', type=str, required=True, help='Path to CSV data file')
    parser.add_argument('--output', type=str, required=True, help='Output path for model')
    parser.add_argument('--model-type', type=str, default='random_forest',
                       choices=['random_forest', 'linear_regression', 'ridge', 'lasso', 'decision_tree'],
                       help='Model type to train')
    parser.add_argument('--target-col', type=str, default='Amount(in rupees)', 
                       help='Target column name')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set size')
    parser.add_argument('--random-state', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    try:
        # Load data
        X, y = load_and_prepare_data(args.data, args.target_col)
        
        # Train model
        results = train_model(X, y, args.model_type, args.test_size, args.random_state)
        
        # Save model
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        joblib.dump(results['model'], args.output)
        
        logger.info(f"Model saved to: {args.output}")
        
        # Print summary
        print(f"\n🎉 Training Complete!")
        print(f"Model Type: {results['model_type']}")
        print(f"Test RMSE: ₹{results['test_rmse']:,.0f}")
        print(f"Test R²: {results['test_r2']:.4f}")
        print(f"Test MAE: ₹{results['test_mae']:,.0f}")
        print(f"Features: {results['n_features']}")
        print(f"Samples: {results['n_samples']}")
        print(f"Model saved to: {args.output}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()