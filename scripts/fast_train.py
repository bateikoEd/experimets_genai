#!/usr/bin/env python3
"""
Fast training script for house price prediction - optimized for the actual dataset.
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import joblib
import logging
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HousePriceModel:
    """Wrapper class for the trained house price prediction model."""
    
    def __init__(self, model, feature_names, label_encoders):
        self.model = model
        self.feature_names = feature_names
        self.label_encoders = label_encoders
    
    def predict(self, X):
        """Make predictions on new data."""
        # X should be a DataFrame with the original column names
        # Extract and process features the same way
        numeric_features = extract_numeric_features(X)
        categorical_features = extract_categorical_features(X)
        
        # Handle missing values in numeric
        for col in numeric_features.columns:
            if col in self.feature_names:
                numeric_features[col] = numeric_features[col].fillna(numeric_features[col].median())
        
        # Encode categorical features
        for col in categorical_features.columns:
            if col in self.label_encoders:
                # Handle unknown categories
                le = self.label_encoders[col]
                # Map unknown values to 0 or most frequent class
                def safe_transform(val):
                    try:
                        return le.transform([str(val)])[0]
                    except ValueError:
                        return 0  # Default for unknown categories
                
                categorical_features[col] = categorical_features[col].astype(str).apply(safe_transform)
        
        # Combine features
        features = pd.concat([numeric_features, categorical_features], axis=1)
        
        # Ensure all expected features are present
        for col in self.feature_names:
            if col not in features.columns:
                features[col] = 0
        
        # Reorder columns to match training
        features = features[self.feature_names]
        
        return self.model.predict(features)


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


def extract_numeric_features(df):
    """Extract key numeric features from the dataset."""
    features = {}
    
    # Parse carpet area 
    if 'Carpet Area' in df.columns:
        def parse_area(area_str):
            if pd.isna(area_str) or not isinstance(area_str, str):
                return np.nan
            # Extract first number found
            match = re.search(r'(\d+\.?\d*)', str(area_str))
            if match:
                return float(match.group(1))
            return np.nan
        
        features['carpet_area'] = df['Carpet Area'].apply(parse_area)
    
    # Parse bathroom count
    if 'Bathroom' in df.columns:
        features['bathroom'] = pd.to_numeric(df['Bathroom'], errors='coerce')
    
    # Parse balcony count  
    if 'Balcony' in df.columns:
        features['balcony'] = pd.to_numeric(df['Balcony'], errors='coerce')
    
    # Parse car parking
    if 'Car Parking' in df.columns:
        features['parking'] = pd.to_numeric(df['Car Parking'], errors='coerce')
    
    return pd.DataFrame(features)


def extract_categorical_features(df):
    """Extract key categorical features."""
    features = {}
    
    # Furnishing status
    if 'Furnishing' in df.columns:
        features['furnishing'] = df['Furnishing'].fillna('Unknown')
    
    # Property status
    if 'Status' in df.columns:
        features['status'] = df['Status'].fillna('Unknown')
    
    # Transaction type
    if 'Transaction' in df.columns:
        features['transaction'] = df['Transaction'].fillna('Unknown')
    
    # Ownership type
    if 'Ownership' in df.columns:
        features['ownership'] = df['Ownership'].fillna('Unknown')
    
    return pd.DataFrame(features)


def main():
    parser = argparse.ArgumentParser(description="Fast House Price Model Training")
    
    parser.add_argument('--data', type=str, required=True, help='Path to CSV data file')
    parser.add_argument('--output', type=str, required=True, help='Output path for model')
    parser.add_argument('--model-type', type=str, default='random_forest',
                       choices=['random_forest', 'linear_regression', 'ridge'],
                       help='Model type to train')
    parser.add_argument('--target-col', type=str, default='Amount(in rupees)', 
                       help='Target column name')
    parser.add_argument('--sample-size', type=int, default=10000,
                       help='Sample size for training (use smaller for faster training)')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set size')
    parser.add_argument('--random-state', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Loading data from: {args.data}")
        
        # Load data
        df = pd.read_csv(args.data)
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
        
        # Parse target
        target = df[args.target_col].apply(parse_indian_price)
        
        # Remove invalid targets
        valid_mask = ~target.isna()
        df_clean = df[valid_mask].copy()
        target_clean = target[valid_mask]
        
        logger.info(f"After cleaning: {len(df_clean)} records")
        logger.info(f"Target range: ₹{target_clean.min():,.0f} to ₹{target_clean.max():,.0f}")
        logger.info(f"Target mean: ₹{target_clean.mean():,.0f}")
        
        # Sample data if requested
        if args.sample_size and len(df_clean) > args.sample_size:
            sample_df = df_clean.sample(n=args.sample_size, random_state=args.random_state)
            sample_target = target_clean.loc[sample_df.index]
            logger.info(f"Using sample of {len(sample_df)} records")
        else:
            sample_df = df_clean
            sample_target = target_clean
        
        # Extract features
        logger.info("Extracting features...")
        numeric_features = extract_numeric_features(sample_df)
        categorical_features = extract_categorical_features(sample_df)
        
        logger.info(f"Numeric features: {list(numeric_features.columns)}")
        logger.info(f"Categorical features: {list(categorical_features.columns)}")
        
        # Combine features
        all_features = pd.concat([numeric_features, categorical_features], axis=1)
        
        # Handle missing values in numeric features
        numeric_cols = numeric_features.columns
        for col in numeric_cols:
            all_features[col] = all_features[col].fillna(all_features[col].median())
        
        # Encode categorical features
        categorical_cols = categorical_features.columns
        label_encoders = {}
        for col in categorical_cols:
            le = LabelEncoder()
            all_features[col] = le.fit_transform(all_features[col].astype(str))
            label_encoders[col] = le
        
        logger.info(f"Final feature set: {all_features.shape[1]} features")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            all_features, sample_target, test_size=args.test_size, random_state=args.random_state
        )
        
        logger.info(f"Data split: {len(X_train)} train, {len(X_test)} test")
        
        # Select and train model
        if args.model_type == 'random_forest':
            model = RandomForestRegressor(n_estimators=100, random_state=args.random_state, n_jobs=-1)
        elif args.model_type == 'linear_regression':
            # Use pipeline with scaling for linear regression
            model = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', LinearRegression())
            ])
        elif args.model_type == 'ridge':
            model = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', Ridge(alpha=1.0))
            ])
        
        logger.info(f"Training {args.model_type} model...")
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Calculate metrics
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        
        logger.info(f"Training Results:")
        logger.info(f"  Train RMSE: ₹{train_rmse:,.0f}")
        logger.info(f"  Test RMSE:  ₹{test_rmse:,.0f}")
        logger.info(f"  Train R²:   {train_r2:.4f}")
        logger.info(f"  Test R²:    {test_r2:.4f}")
        logger.info(f"  Test MAE:   ₹{test_mae:,.0f}")
        
        # Save model and preprocessing info separately
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        # Save the sklearn model
        joblib.dump(model, args.output)
        
        # Save preprocessing info
        preprocessing_info = {
            'feature_names': list(all_features.columns),
            'label_encoders': label_encoders,
            'model_type': args.model_type,
            'feature_medians': {col: all_features[col].median() for col in numeric_cols}
        }
        
        preprocessing_path = args.output.replace('.joblib', '_preprocessing.joblib')
        joblib.dump(preprocessing_info, preprocessing_path)
        
        logger.info(f"Preprocessing info saved to: {preprocessing_path}")
        
        logger.info(f"Model saved to: {args.output}")
        
        # Print summary
        print(f"\n🎉 Training Complete!")
        print(f"Model Type: {args.model_type}")
        print(f"Sample Size: {len(sample_df):,}")
        print(f"Features: {len(all_features.columns)}")
        print(f"Test RMSE: ₹{test_rmse:,.0f}")
        print(f"Test R²: {test_r2:.4f}")
        print(f"Test MAE: ₹{test_mae:,.0f}")
        print(f"Model saved to: {args.output}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()