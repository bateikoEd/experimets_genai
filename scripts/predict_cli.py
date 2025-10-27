#!/usr/bin/env python3
"""
Command-line interface for house price prediction training and inference.
"""

import argparse
import json
import sys
import os
from pathlib import Path
import pandas as pd
import joblib
import logging
from typing import Dict, List, Any, Union
import numpy as np
from sklearn.model_selection import train_test_split

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from data_processing.data_loader import load_house_price_data
    from data_processing.unified_pipeline import UnifiedPreprocessor
    from models.trainer import ModelTrainer
    from models.persistence import ModelPersistence
    from evaluation.evaluator import ModelEvaluator
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory and src/ is in PYTHONPATH")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HousePriceTrainer:
    """CLI trainer for house price models."""
    
    def __init__(self, random_state: int = 42):
        """
        Initialize trainer.
        
        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
    
    def train_model(self, 
                   data_path: str, 
                   output_path: str,
                   model_type: str = 'random_forest',
                   test_size: float = 0.2,
                   target_col: str = 'total_amount') -> Dict[str, Any]:
        """
        Train a house price prediction model.
        
        Args:
            data_path: Path to training data CSV
            output_path: Path to save trained model
            model_type: Type of model to train
            test_size: Test set size (0.0 to 1.0)
            target_col: Name of target column
            
        Returns:
            Training results dictionary
        """
        try:
            logger.info(f"🚀 Starting training with {model_type} model")
            
            # 1. Load and validate data
            logger.info(f"📊 Loading data from: {data_path}")
            df, validation_report = load_house_price_data(data_path, target_col=target_col)
            
            if not validation_report['is_valid']:
                logger.warning("⚠️  Data validation warnings:")
                for warning in validation_report['warnings']:
                    logger.warning(f"   - {warning}")
                for error in validation_report['errors']:
                    logger.error(f"   - {error}")
            
            logger.info(f"✅ Loaded {len(df)} records with {df.shape[1]} features")
            
            # 2. Prepare features and target
            X = df.drop(columns=[target_col])
            y = df[target_col]
            
            logger.info(f"🎯 Target statistics:")
            logger.info(f"   - Mean: ${y.mean():,.2f}")
            logger.info(f"   - Std:  ${y.std():,.2f}")
            logger.info(f"   - Min:  ${y.min():,.2f}")
            logger.info(f"   - Max:  ${y.max():,.2f}")
            
            # 3. Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=self.random_state
            )
            logger.info(f"📊 Data split: {len(X_train)} train, {len(X_test)} test")
            
            # 4. Preprocess features
            logger.info("🔄 Preprocessing features...")
            preprocessor = UnifiedPreprocessor(
                target_col=target_col,
                auto_detect_types=True
            )
            
            preprocessor.fit(X_train)
            X_train_processed = preprocessor.transform(X_train)
            X_test_processed = preprocessor.transform(X_test)
            
            feature_names = preprocessor.get_feature_names()
            logger.info(f"✅ Preprocessing complete: {X_train_processed.shape[1]} features")
            
            # 5. Train model
            logger.info(f"🎯 Training {model_type} model...")
            trainer = ModelTrainer(cv_folds=5, n_jobs=-1, random_state=self.random_state)
            
            if model_type == 'all':
                # Train all models and select best
                results = trainer.train_all_models(X_train_processed, y_train)
                best_name, best_result = trainer.get_best_model()
                model_name = best_name
                trained_model = best_result.model
                training_score = best_result.cv_mean
                
                logger.info(f"🏆 Best model: {best_name} (CV Score: {training_score:.4f})")
                
            else:
                # Train specific model
                from sklearn.ensemble import RandomForestRegressor
                from sklearn.linear_model import LinearRegression, Ridge, Lasso
                from sklearn.tree import DecisionTreeRegressor
                
                model_configs = {
                    'random_forest': {
                        'model': RandomForestRegressor(random_state=self.random_state),
                        'param_grid': {
                            'n_estimators': [100, 200],
                            'max_depth': [10, 15, None],
                            'min_samples_split': [2, 5]
                        }
                    },
                    'linear_regression': {
                        'model': LinearRegression(),
                        'param_grid': {}
                    },
                    'ridge': {
                        'model': Ridge(random_state=self.random_state),
                        'param_grid': {
                            'alpha': [0.1, 1.0, 10.0, 100.0]
                        }
                    },
                    'lasso': {
                        'model': Lasso(random_state=self.random_state),
                        'param_grid': {
                            'alpha': [0.01, 0.1, 1.0, 10.0]
                        }
                    },
                    'decision_tree': {
                        'model': DecisionTreeRegressor(random_state=self.random_state),
                        'param_grid': {
                            'max_depth': [5, 10, 15, None],
                            'min_samples_split': [2, 5, 10]
                        }
                    }
                }
                
                if model_type not in model_configs:
                    raise ValueError(f"Unsupported model type: {model_type}. Choose from: {list(model_configs.keys())}")
                
                config = model_configs[model_type]
                result = trainer.train_single_model(
                    name=model_type,
                    model=config['model'],
                    param_grid=config['param_grid'],
                    X_train=X_train_processed,
                    y_train=y_train
                )
                
                model_name = model_type
                trained_model = result.model
                training_score = result.cv_mean
                
                logger.info(f"✅ Model trained: {model_type} (CV Score: {training_score:.4f})")
            
            # 6. Evaluate on test set
            logger.info("📊 Evaluating on test set...")
            y_pred = trained_model.predict(X_test_processed)
            
            evaluator = ModelEvaluator(feature_names=feature_names)
            test_metrics = evaluator.calculate_regression_metrics(y_test, y_pred)
            
            logger.info("🎯 Test Results:")
            logger.info(f"   - RMSE: ${test_metrics['RMSE']:,.2f}")
            logger.info(f"   - MAE:  ${test_metrics['MAE']:,.2f}")
            logger.info(f"   - R²:   {test_metrics['R2']:.4f}")
            logger.info(f"   - MAPE: {test_metrics['MAPE']:.2f}%")
            
            # 7. Create full pipeline (preprocessor + model)
            from sklearn.pipeline import Pipeline
            
            full_pipeline = Pipeline([
                ('preprocessor', preprocessor),
                ('model', trained_model)
            ])
            
            # 8. Save model
            logger.info(f"💾 Saving model to: {output_path}")
            
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the full pipeline
            joblib.dump(full_pipeline, output_path)
            
            # Also save with ModelPersistence for metadata
            try:
                persistence = ModelPersistence(base_path=os.path.dirname(output_path))
                model_info = {
                    'model': trained_model,
                    'preprocessor': preprocessor,
                    'feature_names': feature_names,
                    'target_name': target_col,
                    'model_type': model_name,
                    'training_score': training_score,
                    'test_metrics': test_metrics,
                    'training_date': pd.Timestamp.now(),
                    'data_path': data_path,
                    'n_samples': len(df),
                    'n_features': len(feature_names)
                }
                
                metadata_path = output_path.replace('.joblib', '_metadata.joblib')
                persistence.save_model(model_info, metadata_path)
                logger.info(f"💾 Metadata saved to: {metadata_path}")
                
            except Exception as e:
                logger.warning(f"⚠️  Could not save metadata: {e}")
            
            logger.info("🎉 Training completed successfully!")
            
            return {
                'model_path': output_path,
                'model_type': model_name,
                'training_score': training_score,
                'test_metrics': test_metrics,
                'n_features': len(feature_names),
                'n_samples': len(df)
            }
            
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            raise


class HousePricePredictor:
    """CLI predictor for house price inference."""
    
    def __init__(self, model_path: str):
        """
        Initialize predictor with trained model.
        
        Args:
            model_path: Path to serialized model pipeline
        """
        self.model_path = model_path
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the trained model pipeline."""
        try:
            self.model = joblib.load(self.model_path)
            logger.info(f"✅ Model loaded from: {self.model_path}")
        except Exception as e:
            raise ValueError(f"❌ Failed to load model from {self.model_path}: {e}")
    
    def predict_json(self, json_input: str) -> List[Dict[str, float]]:
        """
        Make prediction from JSON input.
        
        Args:
            json_input: JSON string with property features
            
        Returns:
            List of prediction dictionaries
        """
        try:
            # Parse JSON
            if isinstance(json_input, str):
                data = json.loads(json_input)
            else:
                data = json_input
            
            # Convert to list if single record
            if isinstance(data, dict):
                data = [data]
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Make predictions
            predictions = self.model.predict(df)
            
            # Format results
            results = []
            for i, pred in enumerate(predictions):
                results.append({
                    "prediction": float(pred),
                    "input_index": i
                })
            
            return results
            
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ Invalid JSON input: {e}")
        except Exception as e:
            raise ValueError(f"❌ Prediction failed: {e}")
    
    def predict_csv(self, csv_path: str, output_path: str = None) -> pd.DataFrame:
        """
        Make predictions from CSV file.
        
        Args:
            csv_path: Path to input CSV file
            output_path: Optional path for output CSV
            
        Returns:
            DataFrame with predictions
        """
        try:
            # Load CSV
            df = pd.read_csv(csv_path)
            logger.info(f"📊 Loaded {len(df)} records from {csv_path}")
            
            # Make predictions
            predictions = self.model.predict(df)
            
            # Add predictions to DataFrame
            df['predicted_price'] = predictions
            
            # Save output if specified
            if output_path:
                df.to_csv(output_path, index=False)
                logger.info(f"💾 Results saved to: {output_path}")
            
            return df
            
        except Exception as e:
            raise ValueError(f"❌ CSV prediction failed: {e}")
    
    def validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean input data.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Validated data dictionary
        """
        # Expected numeric fields (with reasonable ranges)
        numeric_fields = {
            'carpet_area': (100, 10000),
            'bathroom': (1, 10),
            'balcony': (0, 10),
            'parking': (0, 20)
        }
        
        # Expected categorical fields
        categorical_fields = {
            'furnishing': ['Furnished', 'Semi-Furnished', 'Unfurnished'],
            'property_status': ['Ready to Move', 'Under Construction']
        }
        
        validated_data = {}
        
        # Validate numeric fields
        for field, (min_val, max_val) in numeric_fields.items():
            if field in data:
                try:
                    value = float(data[field])
                    if not (min_val <= value <= max_val):
                        logger.warning(f"⚠️  {field} value {value} outside expected range [{min_val}, {max_val}]")
                    validated_data[field] = value
                except (ValueError, TypeError):
                    logger.warning(f"⚠️  Invalid numeric value for {field}: {data[field]}")
        
        # Validate categorical fields  
        for field, valid_values in categorical_fields.items():
            if field in data:
                value = str(data[field])
                if value not in valid_values:
                    logger.warning(f"⚠️  Unexpected value for {field}: {value}. Expected: {valid_values}")
                validated_data[field] = value
        
        # Copy text fields as-is
        text_fields = ['description', 'location', 'property_title', 'society_name']
        for field in text_fields:
            if field in data:
                validated_data[field] = str(data[field])
        
        return validated_data


def create_sample_json() -> str:
    """Create sample JSON input for demonstration."""
    sample = {
        "carpet_area": 1200,
        "bathroom": 2,
        "balcony": 1,
        "furnishing": "Semi-Furnished",
        "property_status": "Ready to Move",
        "description": "Beautiful 2BHK apartment near metro station",
        "location": "Bandra West, Mumbai"
    }
    return json.dumps(sample, indent=2)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="House Price Prediction CLI - Training and Inference",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create subparsers for train and predict commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Training subcommand
    train_parser = subparsers.add_parser(
        'train', 
        help='Train a house price prediction model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Training Examples:
  # Train Random Forest model
  python predict_cli.py train --data data/house_prices.csv --output models/rf_model.joblib
  
  # Train specific model type
  python predict_cli.py train --data data/house_prices.csv --output models/linear_model.joblib --model-type linear_regression
  
  # Train all models and select best
  python predict_cli.py train --data data/house_prices.csv --output models/best_model.joblib --model-type all
        """
    )
    
    train_parser.add_argument(
        '--data', 
        type=str, 
        required=True,
        help='Path to training data CSV file'
    )
    
    train_parser.add_argument(
        '--output', 
        type=str, 
        required=True,
        help='Output path for trained model (e.g., models/model.joblib)'
    )
    
    train_parser.add_argument(
        '--model-type', 
        type=str, 
        default='random_forest',
        choices=['random_forest', 'linear_regression', 'ridge', 'lasso', 'decision_tree', 'all'],
        help='Type of model to train (default: random_forest)'
    )
    
    train_parser.add_argument(
        '--target-col', 
        type=str, 
        default='total_amount',
        help='Name of target column (default: total_amount)'
    )
    
    train_parser.add_argument(
        '--test-size', 
        type=float, 
        default=0.2,
        help='Test set size as fraction (default: 0.2)'
    )
    
    train_parser.add_argument(
        '--random-state', 
        type=int, 
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    # Prediction subcommand
    predict_parser = subparsers.add_parser(
        'predict', 
        help='Make predictions using trained model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Prediction Examples:
  # Predict from JSON
  python predict_cli.py predict --model models/model.joblib --json '{"carpet_area":1200,"bathroom":2}'
  
  # Predict from CSV  
  python predict_cli.py predict --model models/model.joblib --csv input.csv --output predictions.csv
  
  # Show sample JSON format
  python predict_cli.py predict --sample
        """
    )
    
    predict_parser.add_argument(
        '--model', 
        type=str,
        help='Path to trained model file'
    )
    
    predict_parser.add_argument(
        '--json',
        type=str, 
        help='JSON string with property features'
    )
    
    predict_parser.add_argument(
        '--csv',
        type=str,
        help='Path to CSV file with property data'
    )
    
    predict_parser.add_argument(
        '--output',
        type=str,
        help='Output path for CSV predictions'
    )
    
    predict_parser.add_argument(
        '--sample',
        action='store_true',
        help='Show sample JSON input format'
    )
    
    predict_parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate input data before prediction'
    )
    
    args = parser.parse_args()
    
    # Show help if no command specified
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'train':
            # Training mode
            trainer = HousePriceTrainer(random_state=args.random_state)
            
            result = trainer.train_model(
                data_path=args.data,
                output_path=args.output,
                model_type=args.model_type,
                test_size=args.test_size,
                target_col=args.target_col
            )
            
            print("\n🎉 Training Summary:")
            print(f"   - Model Type: {result['model_type']}")
            print(f"   - Training Score: {result['training_score']:.4f}")
            print(f"   - Test RMSE: ${result['test_metrics']['RMSE']:,.2f}")
            print(f"   - Test R²: {result['test_metrics']['R2']:.4f}")
            print(f"   - Features: {result['n_features']}")
            print(f"   - Samples: {result['n_samples']}")
            print(f"   - Model saved to: {result['model_path']}")
            
        elif args.command == 'predict':
            # Prediction mode
            
            # Show sample JSON if requested
            if args.sample:
                print("📋 Sample JSON input format:")
                print(create_sample_json())
                return
            
            # Validate arguments
            if not args.model:
                print("❌ Error: --model is required for prediction")
                predict_parser.print_help()
                sys.exit(1)
            
            if not args.json and not args.csv:
                print("❌ Error: Either --json or --csv is required for prediction")
                predict_parser.print_help()
                sys.exit(1)
            
            # Initialize predictor
            predictor = HousePricePredictor(args.model)
            
            # JSON prediction
            if args.json:
                # Validate input if requested
                if args.validate:
                    data = json.loads(args.json)
                    if isinstance(data, dict):
                        data = predictor.validate_input(data)
                        args.json = json.dumps(data)
                
                results = predictor.predict_json(args.json)
                
                # Output results
                print("🎯 Prediction Results:")
                print(json.dumps(results, indent=2))
            
            # CSV prediction
            elif args.csv:
                results_df = predictor.predict_csv(args.csv, args.output)
                
                print(f"🎯 Prediction Results for {len(results_df)} records:")
                print(f"   - Mean predicted price: ₹{results_df['predicted_price'].mean():,.0f}")
                print(f"   - Min predicted price: ₹{results_df['predicted_price'].min():,.0f}")
                print(f"   - Max predicted price: ₹{results_df['predicted_price'].max():,.0f}")
                
                if not args.output:
                    print("\n📊 First 5 predictions:")
                    print(results_df[['predicted_price']].head().to_string())
    
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Full error traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()