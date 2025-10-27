"""
Model persistence and serialization utilities.
"""

import joblib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class ModelPersistence:
    """
    Utilities for saving and loading trained models with metadata.
    """
    
    @staticmethod
    def save_model(model: Any, 
                   model_path: Union[str, Path],
                   metadata: Optional[Dict[str, Any]] = None,
                   preprocessor: Optional[Any] = None,
                   feature_names: Optional[list] = None) -> Path:
        """
        Save a trained model with metadata and optional preprocessor.
        
        Args:
            model: Trained model to save
            model_path: Path to save model (without extension)
            metadata: Dictionary with model metadata
            preprocessor: Optional data preprocessor
            feature_names: List of feature names
            
        Returns:
            Path to saved model file
        """
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create model package
        model_package = {
            'model': model,
            'preprocessor': preprocessor,
            'feature_names': feature_names,
            'saved_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        # Save model package
        model_file = model_path.with_suffix('.pkl')
        joblib.dump(model_package, model_file)
        
        # Save metadata separately for easy reading
        metadata_file = model_path.with_suffix('_metadata.json')
        with open(metadata_file, 'w') as f:
            json_metadata = {
                'saved_at': model_package['saved_at'],
                'feature_names': feature_names,
                'preprocessor_included': preprocessor is not None,
                'model_type': type(model).__name__,
                'metadata': metadata or {}
            }
            json.dump(json_metadata, f, indent=2)
        
        logger.info(f"💾 Model saved to: {model_file}")
        logger.info(f"📄 Metadata saved to: {metadata_file}")
        
        return model_file
    
    @staticmethod
    def load_model(model_path: Union[str, Path]) -> Tuple[Any, Optional[Any], Optional[list], Dict[str, Any]]:
        """
        Load a saved model with its metadata and preprocessor.
        
        Args:
            model_path: Path to saved model file (with or without extension)
            
        Returns:
            Tuple of (model, preprocessor, feature_names, metadata)
        """
        model_path = Path(model_path)
        
        # Handle path with or without extension
        if model_path.suffix != '.pkl':
            model_path = model_path.with_suffix('.pkl')
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load model package
        model_package = joblib.load(model_path)
        
        # Extract components
        model = model_package['model']
        preprocessor = model_package.get('preprocessor')
        feature_names = model_package.get('feature_names')
        metadata = model_package.get('metadata', {})
        
        # Add loading info to metadata
        metadata['loaded_at'] = datetime.now().isoformat()
        metadata['loaded_from'] = str(model_path)
        
        logger.info(f"📂 Model loaded from: {model_path}")
        logger.info(f"🔧 Model type: {type(model).__name__}")
        logger.info(f"📊 Features: {len(feature_names) if feature_names else 'Unknown'}")
        logger.info(f"🔄 Preprocessor: {'Yes' if preprocessor else 'No'}")
        
        return model, preprocessor, feature_names, metadata
    
    @staticmethod
    def save_training_results(results: Dict[str, Any],
                            output_path: Union[str, Path],
                            best_model_name: Optional[str] = None) -> Path:
        """
        Save complete training results including all models and metadata.
        
        Args:
            results: Dictionary containing training results
            output_path: Path to save results
            best_model_name: Name of the best performing model
            
        Returns:
            Path to saved results directory
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"💾 Saving training results to: {output_path}")
        
        # Save individual models
        models_dir = output_path / "models"
        models_dir.mkdir(exist_ok=True)
        
        model_paths = {}
        
        if 'models' in results:
            for model_name, model_data in results['models'].items():
                model = model_data.get('model')
                if model is not None:
                    # Prepare metadata
                    metadata = {
                        'model_name': model_name,
                        'is_best_model': model_name == best_model_name,
                        'training_results': model_data
                    }
                    
                    # Save model
                    model_path = ModelPersistence.save_model(
                        model=model,
                        model_path=models_dir / model_name,
                        metadata=metadata,
                        preprocessor=results.get('preprocessor'),
                        feature_names=results.get('feature_names')
                    )
                    
                    model_paths[model_name] = str(model_path)
        
        # Save summary results
        summary = {
            'training_completed_at': datetime.now().isoformat(),
            'best_model': best_model_name,
            'model_paths': model_paths,
            'metrics': results.get('metrics', {}),
            'feature_importance': results.get('feature_importance', {}),
            'training_config': results.get('config', {}),
            'data_info': {
                'n_features': len(results.get('feature_names', [])),
                'feature_names': results.get('feature_names', []),
                'preprocessor_included': results.get('preprocessor') is not None
            }
        }
        
        summary_file = output_path / "training_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📄 Training summary saved to: {summary_file}")
        logger.info(f"🏆 Best model: {best_model_name}")
        
        return output_path
    
    @staticmethod
    def load_training_results(results_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load complete training results.
        
        Args:
            results_path: Path to saved training results
            
        Returns:
            Dictionary with loaded training results
        """
        results_path = Path(results_path)
        summary_file = results_path / "training_summary.json"
        
        if not summary_file.exists():
            raise FileNotFoundError(f"Training summary not found: {summary_file}")
        
        # Load summary
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        # Load models
        models = {}
        for model_name, model_path in summary.get('model_paths', {}).items():
            try:
                model, preprocessor, feature_names, metadata = ModelPersistence.load_model(model_path)
                models[model_name] = {
                    'model': model,
                    'preprocessor': preprocessor,
                    'feature_names': feature_names,
                    'metadata': metadata
                }
            except Exception as e:
                logger.warning(f"Failed to load model {model_name}: {e}")
                continue
        
        results = {
            'models': models,
            'summary': summary,
            'best_model': summary.get('best_model'),
            'metrics': summary.get('metrics', {}),
            'feature_importance': summary.get('feature_importance', {}),
            'loaded_at': datetime.now().isoformat()
        }
        
        logger.info(f"📂 Training results loaded from: {results_path}")
        logger.info(f"🔧 Models loaded: {list(models.keys())}")
        
        return results
    
    @staticmethod
    def get_model_info(model_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get model information without loading the full model.
        
        Args:
            model_path: Path to model file
            
        Returns:
            Dictionary with model information
        """
        model_path = Path(model_path)
        
        # Try to load metadata file first
        metadata_file = model_path.with_suffix('_metadata.json')
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        
        # Fallback: load model package headers
        if model_path.suffix != '.pkl':
            model_path = model_path.with_suffix('.pkl')
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load minimal info from joblib without fully deserializing
        try:
            with open(model_path, 'rb') as f:
                # This is a simplified approach - in practice, you might want to use
                # joblib's ability to load only metadata if the format supports it
                model_package = joblib.load(model_path)
                
                info = {
                    'saved_at': model_package.get('saved_at'),
                    'feature_names': model_package.get('feature_names'),
                    'preprocessor_included': model_package.get('preprocessor') is not None,
                    'model_type': type(model_package['model']).__name__,
                    'metadata': model_package.get('metadata', {})
                }
                
                return info
                
        except Exception as e:
            logger.error(f"Failed to read model info: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def list_saved_models(models_dir: Union[str, Path]) -> list:
        """
        List all saved models in a directory.
        
        Args:
            models_dir: Directory containing saved models
            
        Returns:
            List of dictionaries with model information
        """
        models_dir = Path(models_dir)
        
        if not models_dir.exists():
            logger.warning(f"Models directory not found: {models_dir}")
            return []
        
        models = []
        
        for model_file in models_dir.glob("*.pkl"):
            try:
                info = ModelPersistence.get_model_info(model_file)
                info['file_path'] = str(model_file)
                info['file_size'] = model_file.stat().st_size
                models.append(info)
            except Exception as e:
                logger.warning(f"Failed to read info for {model_file}: {e}")
                continue
        
        # Sort by saved date (newest first)
        models.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
        
        return models


class ModelPredictor:
    """
    Convenient wrapper for making predictions with saved models.
    """
    
    def __init__(self, model_path: Union[str, Path]):
        """
        Initialize predictor with saved model.
        
        Args:
            model_path: Path to saved model
        """
        self.model, self.preprocessor, self.feature_names, self.metadata = (
            ModelPersistence.load_model(model_path)
        )
        
    def predict(self, X: Union[np.ndarray, dict, list]) -> np.ndarray:
        """
        Make predictions on new data.
        
        Args:
            X: Input data (array, dict, or list)
            
        Returns:
            Predictions array
        """
        # Handle different input formats
        if isinstance(X, (dict, list)):
            # Convert to numpy array if needed
            if isinstance(X, dict):
                # Single prediction from dict
                if self.feature_names:
                    X = np.array([[X.get(name, 0) for name in self.feature_names]])
                else:
                    raise ValueError("Feature names required for dict input")
            elif isinstance(X, list):
                # Handle list of values or list of dicts
                if len(X) > 0 and isinstance(X[0], dict):
                    # List of dicts
                    if self.feature_names:
                        X = np.array([[item.get(name, 0) for name in self.feature_names] 
                                     for item in X])
                    else:
                        raise ValueError("Feature names required for dict input")
                else:
                    # Simple list of values - assume single prediction
                    X = np.array([X])
        
        # Apply preprocessing if available
        if self.preprocessor is not None:
            X = self.preprocessor.transform(X)
        
        # Make predictions
        predictions = self.model.predict(X)
        
        return predictions
    
    def predict_with_confidence(self, X: Union[np.ndarray, dict, list]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Make predictions with confidence intervals if supported.
        
        Args:
            X: Input data
            
        Returns:
            Tuple of (predictions, confidence_intervals)
        """
        predictions = self.predict(X)
        
        # Try to get prediction intervals for ensemble methods
        confidence_intervals = None
        
        if hasattr(self.model, 'estimators_'):
            # For ensemble methods, calculate prediction std
            try:
                # Prepare data
                X_processed = X
                if isinstance(X, (dict, list)):
                    X_processed = self.predict(X)  # This handles the conversion
                    X_processed = X  # Reset for proper processing
                
                if self.preprocessor is not None:
                    X_processed = self.preprocessor.transform(X_processed)
                
                # Get predictions from all estimators
                individual_predictions = np.array([
                    estimator.predict(X_processed) 
                    for estimator in self.model.estimators_
                ])
                
                # Calculate confidence intervals (mean ± 1.96 * std)
                pred_std = np.std(individual_predictions, axis=0)
                confidence_intervals = 1.96 * pred_std
                
            except Exception as e:
                logger.debug(f"Could not calculate confidence intervals: {e}")
        
        return predictions, confidence_intervals
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            'model_type': type(self.model).__name__,
            'feature_names': self.feature_names,
            'n_features': len(self.feature_names) if self.feature_names else None,
            'has_preprocessor': self.preprocessor is not None,
            'metadata': self.metadata
        }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Generate sample data and model
    np.random.seed(42)
    X = np.random.randn(100, 5)
    y = np.sum(X[:, :3], axis=1) + np.random.randn(100) * 0.1
    
    # Simple mock model
    class MockModel:
        def __init__(self):
            self.coef_ = np.random.randn(5)
            
        def fit(self, X, y):
            return self
            
        def predict(self, X):
            return X @ self.coef_
    
    # Create and train model
    model = MockModel().fit(X, y)
    feature_names = [f'feature_{i}' for i in range(5)]
    
    # Test model persistence
    model_path = Path("test_model")
    
    # Save model
    saved_path = ModelPersistence.save_model(
        model=model,
        model_path=model_path,
        metadata={'test_model': True, 'accuracy': 0.95},
        feature_names=feature_names
    )
    
    # Load model
    loaded_model, preprocessor, loaded_features, metadata = ModelPersistence.load_model(saved_path)
    
    print(f"✅ Model saved and loaded successfully!")
    print(f"📊 Features: {len(loaded_features)}")
    print(f"📄 Metadata: {metadata}")
    
    # Test predictor
    predictor = ModelPredictor(saved_path)
    
    # Test prediction with dict
    test_dict = {f'feature_{i}': np.random.randn() for i in range(5)}
    prediction = predictor.predict(test_dict)
    print(f"🔮 Prediction: {prediction[0]:.4f}")
    
    # Clean up test file
    if saved_path.exists():
        saved_path.unlink()
    metadata_file = saved_path.with_suffix('_metadata.json')
    if metadata_file.exists():
        metadata_file.unlink()