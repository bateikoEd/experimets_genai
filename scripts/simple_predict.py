#!/usr/bin/env python3
"""
Simple prediction script that works with the fast-trained models.
"""

import argparse
import pandas as pd
import numpy as np
import joblib
import json
import re
from sklearn.preprocessing import LabelEncoder


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
    if 'Carpet Area' in df.columns or 'carpet_area' in df.columns:
        area_col = 'Carpet Area' if 'Carpet Area' in df.columns else 'carpet_area'
        def parse_area(area_str):
            if pd.isna(area_str) or not isinstance(area_str, str):
                return np.nan
            # Extract first number found
            match = re.search(r'(\d+\.?\d*)', str(area_str))
            if match:
                return float(match.group(1))
            return np.nan
        
        features['carpet_area'] = df[area_col].apply(parse_area)
    
    # Parse bathroom count
    if 'Bathroom' in df.columns or 'bathroom' in df.columns:
        bath_col = 'Bathroom' if 'Bathroom' in df.columns else 'bathroom'
        features['bathroom'] = pd.to_numeric(df[bath_col], errors='coerce')
    
    # Parse balcony count  
    if 'Balcony' in df.columns or 'balcony' in df.columns:
        balcony_col = 'Balcony' if 'Balcony' in df.columns else 'balcony'
        features['balcony'] = pd.to_numeric(df[balcony_col], errors='coerce')
    
    # Parse car parking
    if 'Car Parking' in df.columns or 'parking' in df.columns:
        parking_col = 'Car Parking' if 'Car Parking' in df.columns else 'parking'
        features['parking'] = pd.to_numeric(df[parking_col], errors='coerce')
    
    return pd.DataFrame(features)


def extract_categorical_features(df):
    """Extract key categorical features."""
    features = {}
    
    # Furnishing status
    if 'Furnishing' in df.columns or 'furnishing' in df.columns:
        furn_col = 'Furnishing' if 'Furnishing' in df.columns else 'furnishing'
        features['furnishing'] = df[furn_col].fillna('Unknown')
    
    # Property status
    if 'Status' in df.columns or 'status' in df.columns:
        status_col = 'Status' if 'Status' in df.columns else 'status'
        features['status'] = df[status_col].fillna('Unknown')
    
    # Transaction type
    if 'Transaction' in df.columns or 'transaction' in df.columns:
        trans_col = 'Transaction' if 'Transaction' in df.columns else 'transaction'
        features['transaction'] = df[trans_col].fillna('Unknown')
    
    # Ownership type
    if 'Ownership' in df.columns or 'ownership' in df.columns:
        own_col = 'Ownership' if 'Ownership' in df.columns else 'ownership'
        features['ownership'] = df[own_col].fillna('Unknown')
    
    return pd.DataFrame(features)


def preprocess_for_prediction(df, preprocessing_info):
    """Preprocess data for prediction using saved preprocessing info."""
    
    # Extract features
    numeric_features = extract_numeric_features(df)
    categorical_features = extract_categorical_features(df)
    
    # Handle missing values in numeric using saved medians
    for col in numeric_features.columns:
        if col in preprocessing_info['feature_medians']:
            median_val = preprocessing_info['feature_medians'][col]
            numeric_features[col] = numeric_features[col].fillna(median_val)
        else:
            numeric_features[col] = numeric_features[col].fillna(0)
    
    # Encode categorical features using saved encoders
    for col in categorical_features.columns:
        if col in preprocessing_info['label_encoders']:
            le = preprocessing_info['label_encoders'][col]
            # Handle unknown categories
            def safe_transform(val):
                try:
                    return le.transform([str(val)])[0]
                except ValueError:
                    return 0  # Default for unknown categories
            
            categorical_features[col] = categorical_features[col].astype(str).apply(safe_transform)
        else:
            categorical_features[col] = 0
    
    # Combine features
    features = pd.concat([numeric_features, categorical_features], axis=1)
    
    # Ensure all expected features are present
    for col in preprocessing_info['feature_names']:
        if col not in features.columns:
            features[col] = 0
    
    # Reorder columns to match training
    features = features[preprocessing_info['feature_names']]
    
    return features


def main():
    parser = argparse.ArgumentParser(description="House Price Prediction")
    
    parser.add_argument('--model', type=str, help='Path to trained model')
    parser.add_argument('--json', type=str, help='JSON input for single prediction')  
    parser.add_argument('--csv', type=str, help='CSV file for batch prediction')
    parser.add_argument('--output', type=str, help='Output CSV file for batch predictions')
    parser.add_argument('--sample', action='store_true', help='Show sample input format')
    
    args = parser.parse_args()
    
    if args.sample:
        sample = {
            "Carpet Area": "1200 sq ft",
            "Bathroom": 2,
            "Balcony": 1,
            "Car Parking": 1,
            "Furnishing": "Semi-Furnished",
            "Status": "Ready to Move", 
            "Transaction": "New Property",
            "Ownership": "Freehold"
        }
        print("Sample JSON input:")
        print(json.dumps(sample, indent=2))
        return
    
    try:
        # Load model and preprocessing info
        model = joblib.load(args.model)
        preprocessing_path = args.model.replace('.joblib', '_preprocessing.joblib')
        preprocessing_info = joblib.load(preprocessing_path)
        
        print(f"✅ Model loaded: {args.model}")
        print(f"Model type: {preprocessing_info['model_type']}")
        print(f"Features: {len(preprocessing_info['feature_names'])}")
        
        if args.json:
            # Single prediction from JSON
            data = json.loads(args.json)
            df = pd.DataFrame([data])
            
            # Preprocess
            processed_features = preprocess_for_prediction(df, preprocessing_info)
            
            # Predict
            prediction = model.predict(processed_features)[0]
            
            print(f"\n🎯 Prediction: ₹{prediction:,.0f}")
            
        elif args.csv:
            # Batch prediction from CSV
            df = pd.read_csv(args.csv)
            print(f"📊 Loaded {len(df)} records for prediction")
            
            # Preprocess
            processed_features = preprocess_for_prediction(df, preprocessing_info)
            
            # Predict
            predictions = model.predict(processed_features)
            
            # Add predictions to dataframe
            df['predicted_price'] = predictions
            
            # Save if output specified
            if args.output:
                df.to_csv(args.output, index=False)
                print(f"💾 Results saved to: {args.output}")
            
            # Show summary
            print(f"\n🎯 Prediction Summary:")
            print(f"Records: {len(predictions)}")
            print(f"Mean price: ₹{predictions.mean():,.0f}")
            print(f"Min price: ₹{predictions.min():,.0f}")
            print(f"Max price: ₹{predictions.max():,.0f}")
            
            if not args.output:
                print(f"\nFirst 5 predictions:")
                print(df[['predicted_price']].head())
        
        else:
            print("❌ Error: Specify either --json or --csv for input")
            parser.print_help()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()