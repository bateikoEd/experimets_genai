"""
Enhanced model trainer with experiment tracking integration.
"""

from ..models.trainer import ModelTrainer, ModelResult
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class ExperimentModelTrainer(ModelTrainer):
    """
    Enhanced ModelTrainer with Weights & Biases experiment tracking.
    """
    
    def __init__(self, 
                 cv_folds: int = 5,
                 random_state: int = 42,
                 scoring: str = 'neg_mean_squared_error',
                 n_jobs: int = -1,
                 experiment_tracker: Optional[Any] = None):
        """
        Initialize enhanced model trainer with experiment tracking.
        
        Args:
            cv_folds: Number of cross-validation folds
            random_state: Random state for reproducibility
            scoring: Scoring metric for cross-validation
            n_jobs: Number of parallel jobs (-1 for all cores)
            experiment_tracker: ExperimentTracker instance for logging
        """
        super().__init__(cv_folds, random_state, scoring, n_jobs)
        self.experiment_tracker = experiment_tracker
        
    def train_all_models(self, 
                        X: np.ndarray, 
                        y: np.ndarray,
                        X_test: Optional[np.ndarray] = None,
                        y_test: Optional[np.ndarray] = None,
                        tune_hyperparameters: bool = True,
                        log_to_experiment: bool = True) -> Dict[str, ModelResult]:
        """
        Train all models with experiment tracking.
        
        Args:
            X: Training features
            y: Training targets
            X_test: Optional test features for final evaluation
            y_test: Optional test targets for final evaluation
            tune_hyperparameters: Whether to perform hyperparameter tuning
            log_to_experiment: Whether to log results to experiment tracker
            
        Returns:
            Dictionary mapping model names to ModelResult objects
        """
        # Log experiment configuration if tracker available
        if log_to_experiment and self.experiment_tracker:
            config = {
                'cv_folds': self.cv_folds,
                'scoring': self.scoring,
                'tune_hyperparameters': tune_hyperparameters,
                'n_samples': len(X),
                'n_features': X.shape[1] if hasattr(X, 'shape') else len(X[0]),
                'has_test_set': X_test is not None
            }
            self.experiment_tracker.log_config(config, prefix='training')
        
        # Train models using parent class
        results = super().train_all_models(X, y, X_test, y_test, tune_hyperparameters)
        
        # Log results to experiment tracker
        if log_to_experiment and self.experiment_tracker:
            self._log_training_results(results, X, y, X_test, y_test)
        
        return results
    
    def _log_training_results(self, 
                            results: Dict[str, ModelResult],
                            X: np.ndarray,
                            y: np.ndarray,
                            X_test: Optional[np.ndarray] = None,
                            y_test: Optional[np.ndarray] = None):
        """
        Log training results to experiment tracker.
        
        Args:
            results: Training results dictionary
            X: Training features
            y: Training targets  
            X_test: Optional test features
            y_test: Optional test targets
        """
        logger.info("📊 Logging training results to experiment tracker...")
        
        # Log overall training metrics
        training_metrics = {
            'n_models_trained': len(results),
            'total_training_time': sum(r.training_time for r in results.values()),
            'best_cv_score': max(r.cv_mean for r in results.values()),
            'worst_cv_score': min(r.cv_mean for r in results.values())
        }
        
        self.experiment_tracker.log_metrics(training_metrics)
        
        # Log individual model results
        for model_name, result in results.items():
            
            # Prepare model metrics
            model_metrics = {
                'cv_mean_score': result.cv_mean,
                'cv_std_score': result.cv_std,
                'training_time': result.training_time,
            }
            
            # Add test score if available
            if result.test_score is not None:
                model_metrics['test_score'] = result.test_score
            
            # Convert CV scores to RMSE if using neg_mean_squared_error
            if self.scoring == 'neg_mean_squared_error':
                model_metrics['cv_rmse_mean'] = np.sqrt(-result.cv_mean)
                model_metrics['cv_rmse_std'] = result.cv_std / (2 * np.sqrt(-result.cv_mean))
                
                if result.test_score is not None:
                    model_metrics['test_rmse'] = np.sqrt(-result.test_score)
            
            # Extract feature importance if available
            feature_importance = None
            if hasattr(result.model, 'feature_importances_'):
                # For tree-based models
                feature_importance = {
                    f'feature_{i}': float(importance) 
                    for i, importance in enumerate(result.model.feature_importances_)
                }
            elif hasattr(result.model, 'coef_'):
                # For linear models
                feature_importance = {
                    f'feature_{i}': float(abs(coef)) 
                    for i, coef in enumerate(result.model.coef_)
                }
            
            # Log comprehensive model results
            self.experiment_tracker.log_model_results(
                model_name=model_name,
                metrics=model_metrics,
                hyperparameters=result.best_params,
                feature_importance=feature_importance
            )
        
        # Find and log best model
        best_model_name = max(results.keys(), key=lambda k: results[k].cv_mean)
        best_result = results[best_model_name]
        
        self.experiment_tracker.log_metrics({
            'best_model': best_model_name,
            'best_model_cv_score': best_result.cv_mean,
            'best_model_training_time': best_result.training_time
        })
        
        logger.info(f"🏆 Best model: {best_model_name} (CV score: {best_result.cv_mean:.4f})")
    
    def create_training_report(self, 
                             results: Dict[str, ModelResult],
                             output_dir: str = "artifacts/training",
                             save_models: bool = True) -> Path:
        """
        Create comprehensive training report with experiment tracking.
        
        Args:
            results: Training results dictionary
            output_dir: Output directory for reports
            save_models: Whether to save trained models
            
        Returns:
            Path to created report directory
        """
        from ..models.persistence import ModelPersistence
        from ..evaluation.evaluator import ModelEvaluator
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📋 Creating training report in: {output_path}")
        
        # Find best model
        best_model_name = max(results.keys(), key=lambda k: results[k].cv_mean)
        best_result = results[best_model_name]
        
        # Save models if requested
        model_paths = {}
        if save_models:
            models_dir = output_path / "models"
            models_dir.mkdir(exist_ok=True)
            
            for model_name, result in results.items():
                try:
                    # Prepare metadata
                    metadata = {
                        'model_name': model_name,
                        'cv_mean': result.cv_mean,
                        'cv_std': result.cv_std,
                        'training_time': result.training_time,
                        'is_best_model': model_name == best_model_name,
                        'best_params': result.best_params,
                        'test_score': result.test_score
                    }
                    
                    # Save model
                    model_path = ModelPersistence.save_model(
                        model=result.model,
                        model_path=models_dir / model_name,
                        metadata=metadata
                    )
                    
                    model_paths[model_name] = str(model_path)
                    
                    # Log model artifact to experiment tracker
                    if self.experiment_tracker:
                        self.experiment_tracker.log_artifact(
                            artifact_path=model_path,
                            name=f"{model_name}_model",
                            artifact_type="model",
                            description=f"Trained {model_name} model",
                            aliases=["best"] if model_name == best_model_name else None
                        )
                    
                except Exception as e:
                    logger.warning(f"Failed to save model {model_name}: {e}")
                    continue
        
        # Create summary report
        import json
        summary = {
            'training_summary': {
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'n_models': len(results),
                'best_model': best_model_name,
                'best_cv_score': best_result.cv_mean,
                'total_training_time': sum(r.training_time for r in results.values()),
                'configuration': {
                    'cv_folds': self.cv_folds,
                    'scoring': self.scoring,
                    'random_state': self.random_state
                }
            },
            'model_results': {
                name: {
                    'cv_mean': float(result.cv_mean),
                    'cv_std': float(result.cv_std),
                    'training_time': float(result.training_time),
                    'best_params': result.best_params,
                    'test_score': float(result.test_score) if result.test_score else None
                }
                for name, result in results.items()
            },
            'model_paths': model_paths
        }
        
        summary_file = output_path / "training_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Log training report artifact
        if self.experiment_tracker:
            self.experiment_tracker.log_artifact(
                artifact_path=output_path,
                name="training_report",
                artifact_type="report",
                description="Complete training report with models and metrics"
            )
        
        logger.info(f"📋 Training report saved: {summary_file}")
        logger.info(f"🏆 Best model: {best_model_name}")
        logger.info(f"⏱️  Total training time: {sum(r.training_time for r in results.values()):.2f}s")
        
        return output_path


def train_with_experiment_tracking(X: np.ndarray,
                                 y: np.ndarray,
                                 X_test: Optional[np.ndarray] = None,
                                 y_test: Optional[np.ndarray] = None,
                                 experiment_config: Optional[Dict[str, Any]] = None,
                                 experiment_name: Optional[str] = None,
                                 output_dir: str = "artifacts/training") -> Tuple[Dict[str, ModelResult], Path]:
    """
    Complete training pipeline with experiment tracking.
    
    Args:
        X: Training features
        y: Training targets
        X_test: Optional test features
        y_test: Optional test targets
        experiment_config: Experiment configuration dictionary
        experiment_name: Optional experiment name
        output_dir: Output directory for artifacts
        
    Returns:
        Tuple of (training results, report path)
    """
    from ..experiment_tracking import create_experiment_tracker, MLExperimentContext
    
    # Default experiment configuration
    default_config = {
        'model_training': {
            'cv_folds': 5,
            'scoring': 'neg_mean_squared_error',
            'tune_hyperparameters': True,
            'random_state': 42
        },
        'wandb': {
            'project': 'house-price-prediction',
            'tags': ['model-training', 'automated'],
            'offline': False
        }
    }
    
    # Merge with provided config
    if experiment_config:
        config = {**default_config, **experiment_config}
    else:
        config = default_config
    
    # Create experiment tracker
    tracker = create_experiment_tracker(config, experiment_name)
    
    # Training with experiment context
    with MLExperimentContext(tracker) as exp:
        
        # Create enhanced trainer
        trainer_config = config['model_training']
        trainer = ExperimentModelTrainer(
            cv_folds=trainer_config['cv_folds'],
            scoring=trainer_config['scoring'],
            random_state=trainer_config['random_state'],
            experiment_tracker=exp
        )
        
        # Train models
        logger.info("🚀 Starting model training with experiment tracking...")
        results = trainer.train_all_models(
            X=X,
            y=y,
            X_test=X_test,
            y_test=y_test,
            tune_hyperparameters=trainer_config['tune_hyperparameters']
        )
        
        # Create training report
        report_path = trainer.create_training_report(
            results=results,
            output_dir=output_dir,
            save_models=True
        )
        
        logger.info("✅ Training completed with experiment tracking!")
        
        return results, report_path


if __name__ == "__main__":
    # Example usage
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Generate sample data
    np.random.seed(42)
    n_samples = 1000
    n_features = 10
    
    X = np.random.randn(n_samples, n_features)
    y = np.sum(X[:, :3], axis=1) + np.random.randn(n_samples) * 0.1
    
    # Split data manually to avoid sklearn import issues
    split_idx = int(0.8 * len(X))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Test training with experiment tracking
    try:
        results, report_path = train_with_experiment_tracking(
            X=X_train,
            y=y_train,
            X_test=X_test,
            y_test=y_test,
            experiment_name="test_experiment_tracking"
        )
        
        print(f"✅ Training completed!")
        print(f"📊 Trained {len(results)} models")
        print(f"📋 Report saved to: {report_path}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise