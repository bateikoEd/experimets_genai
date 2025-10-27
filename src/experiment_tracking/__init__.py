"""
Experiment tracking and logging utilities using Weights & Biases.
"""

# Import main classes after the implementation
from .enhanced_trainer import ExperimentModelTrainer, train_with_experiment_tracking

import logging
import json
import os
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

# Handle optional wandb import
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    logger.warning("W&B not available. Install with: pip install wandb")


class ExperimentTracker:
    """
    Weights & Biases experiment tracking integration for ML pipeline.
    """
    
    def __init__(self, 
                 project_name: str = "house-price-prediction",
                 entity: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 name: Optional[str] = None,
                 offline: bool = False):
        """
        Initialize experiment tracker.
        
        Args:
            project_name: W&B project name
            entity: W&B entity (team/user)
            config: Experiment configuration dictionary
            tags: List of tags for the experiment
            notes: Experiment description/notes
            name: Experiment run name
            offline: Run in offline mode
        """
        self.project_name = project_name
        self.entity = entity
        self.config = config or {}
        self.tags = tags or []
        self.notes = notes
        self.name = name
        self.offline = offline
        self.run = None
        self._initialized = False
        
        # Fallback storage for offline/no-wandb mode
        self.local_logs = {
            'metrics': {},
            'config': self.config.copy(),
            'artifacts': [],
            'model_metrics': {}
        }
    
    def init_experiment(self, 
                       resume: Optional[str] = None,
                       reinit: bool = True) -> bool:
        """
        Initialize W&B experiment run.
        
        Args:
            resume: Resume run ID or "allow", "must", "never"
            reinit: Whether to reinitialize if already initialized
            
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized and not reinit:
            logger.info("Experiment already initialized")
            return True
        
        if not WANDB_AVAILABLE:
            logger.warning("W&B not available, using local logging only")
            self._initialized = True
            return False
        
        try:
            # Handle API key
            if not os.getenv('WANDB_API_KEY'):
                logger.info("WANDB_API_KEY not set, running in offline mode")
                self.offline = True
            
            # Initialize run
            self.run = wandb.init(
                project=self.project_name,
                entity=self.entity,
                config=self.config,
                tags=self.tags,
                notes=self.notes,
                name=self.name,
                resume=resume,
                mode="offline" if self.offline else "online",
                reinit=reinit
            )
            
            self._initialized = True
            logger.info(f"✅ W&B experiment initialized: {self.run.name if self.run else 'offline'}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize W&B: {e}")
            logger.info("Falling back to local logging")
            self._initialized = True
            return False
    
    def log_config(self, config: Dict[str, Any], prefix: str = ""):
        """
        Log experiment configuration.
        
        Args:
            config: Configuration dictionary
            prefix: Optional prefix for config keys
        """
        prefixed_config = {f"{prefix}.{k}" if prefix else k: v for k, v in config.items()}
        
        # Update local config
        self.local_logs['config'].update(prefixed_config)
        
        # Log to W&B if available
        if self.run is not None:
            try:
                wandb.config.update(prefixed_config)
                logger.debug(f"Logged config to W&B: {list(prefixed_config.keys())}")
            except Exception as e:
                logger.warning(f"Failed to log config to W&B: {e}")
        
        logger.info(f"📝 Logged configuration: {len(prefixed_config)} parameters")
    
    def log_metrics(self, 
                   metrics: Dict[str, Union[float, int]], 
                   step: Optional[int] = None,
                   commit: bool = True):
        """
        Log metrics to experiment tracker.
        
        Args:
            metrics: Dictionary of metric name -> value
            step: Optional step number
            commit: Whether to commit the metrics immediately
        """
        # Store locally
        if step is not None:
            if step not in self.local_logs['metrics']:
                self.local_logs['metrics'][step] = {}
            self.local_logs['metrics'][step].update(metrics)
        else:
            # Store as latest metrics
            self.local_logs['metrics'].update(metrics)
        
        # Log to W&B if available
        if self.run is not None:
            try:
                wandb.log(metrics, step=step, commit=commit)
                logger.debug(f"Logged metrics to W&B: {list(metrics.keys())}")
            except Exception as e:
                logger.warning(f"Failed to log metrics to W&B: {e}")
        
        logger.info(f"📊 Logged metrics: {', '.join(f'{k}={v:.4f}' if isinstance(v, float) else f'{k}={v}' for k, v in metrics.items())}")
    
    def log_model_results(self, 
                         model_name: str,
                         metrics: Dict[str, float],
                         hyperparameters: Optional[Dict[str, Any]] = None,
                         feature_importance: Optional[Dict[str, float]] = None):
        """
        Log comprehensive model results.
        
        Args:
            model_name: Name of the model
            metrics: Model performance metrics
            hyperparameters: Model hyperparameters
            feature_importance: Feature importance scores
        """
        # Prepare model data
        model_data = {
            'model_name': model_name,
            'metrics': metrics,
            'hyperparameters': hyperparameters or {},
            'feature_importance': feature_importance or {}
        }
        
        # Store locally
        self.local_logs['model_metrics'][model_name] = model_data
        
        # Create prefixed metrics for W&B
        prefixed_metrics = {f"{model_name}.{k}": v for k, v in metrics.items()}
        
        # Log metrics
        self.log_metrics(prefixed_metrics)
        
        # Log hyperparameters as config
        if hyperparameters:
            self.log_config(hyperparameters, prefix=f"models.{model_name}")
        
        # Log feature importance as table if available
        if feature_importance and self.run is not None:
            try:
                # Create feature importance table
                importance_data = [
                    [feature, importance] 
                    for feature, importance in sorted(feature_importance.items(), 
                                                    key=lambda x: abs(x[1]), reverse=True)[:20]
                ]
                
                table = wandb.Table(
                    data=importance_data,
                    columns=["Feature", "Importance"]
                )
                
                wandb.log({f"{model_name}_feature_importance": table})
                logger.debug(f"Logged feature importance table for {model_name}")
                
            except Exception as e:
                logger.warning(f"Failed to log feature importance table: {e}")
        
        logger.info(f"🎯 Logged {model_name} results: {len(metrics)} metrics")
    
    def log_artifact(self, 
                    artifact_path: Union[str, Path],
                    name: Optional[str] = None,
                    artifact_type: str = "model",
                    description: Optional[str] = None,
                    aliases: Optional[List[str]] = None):
        """
        Log file artifact to experiment tracker.
        
        Args:
            artifact_path: Path to artifact file/directory
            name: Artifact name (defaults to filename)
            artifact_type: Type of artifact ("model", "dataset", "plot", etc.)
            description: Artifact description
            aliases: List of aliases for the artifact
        """
        artifact_path = Path(artifact_path)
        
        if not artifact_path.exists():
            logger.warning(f"Artifact path does not exist: {artifact_path}")
            return
        
        artifact_name = name or artifact_path.name
        
        # Store locally
        self.local_logs['artifacts'].append({
            'path': str(artifact_path),
            'name': artifact_name,
            'type': artifact_type,
            'description': description
        })
        
        # Log to W&B if available
        if self.run is not None:
            try:
                artifact = wandb.Artifact(
                    name=artifact_name,
                    type=artifact_type,
                    description=description
                )
                
                if artifact_path.is_file():
                    artifact.add_file(str(artifact_path))
                else:
                    artifact.add_dir(str(artifact_path))
                
                self.run.log_artifact(artifact, aliases=aliases)
                logger.debug(f"Logged artifact to W&B: {artifact_name}")
                
            except Exception as e:
                logger.warning(f"Failed to log artifact to W&B: {e}")
        
        logger.info(f"📦 Logged artifact: {artifact_name} ({artifact_type})")
    
    def log_plot(self, 
                figure,
                name: str,
                description: Optional[str] = None):
        """
        Log matplotlib figure to experiment tracker.
        
        Args:
            figure: Matplotlib figure object
            name: Plot name
            description: Plot description
        """
        # Log to W&B if available
        if self.run is not None:
            try:
                wandb.log({name: wandb.Image(figure, caption=description)})
                logger.debug(f"Logged plot to W&B: {name}")
            except Exception as e:
                logger.warning(f"Failed to log plot to W&B: {e}")
        
        logger.info(f"📈 Logged plot: {name}")
    
    def save_local_logs(self, output_path: Union[str, Path] = "artifacts/experiments"):
        """
        Save experiment logs locally as JSON.
        
        Args:
            output_path: Directory to save logs
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        run_id = self.run.id if self.run else "local"
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"experiment_{run_id}_{timestamp}.json"
        
        log_file = output_path / filename
        
        # Prepare logs for JSON serialization
        serializable_logs = {}
        for key, value in self.local_logs.items():
            if isinstance(value, dict):
                # Convert numpy types to native Python types
                serializable_logs[key] = {
                    k: float(v) if isinstance(v, (np.floating, np.integer)) else v
                    for k, v in value.items()
                }
            else:
                serializable_logs[key] = value
        
        # Add metadata
        serializable_logs['metadata'] = {
            'project_name': self.project_name,
            'run_id': run_id,
            'run_name': self.run.name if self.run else None,
            'tags': self.tags,
            'notes': self.notes,
            'wandb_available': WANDB_AVAILABLE,
            'offline_mode': self.offline
        }
        
        # Save logs
        with open(log_file, 'w') as f:
            json.dump(serializable_logs, f, indent=2)
        
        logger.info(f"💾 Saved local experiment logs: {log_file}")
        
        return log_file
    
    def finish_experiment(self, 
                         save_local: bool = True,
                         exit_code: Optional[int] = None):
        """
        Finish and clean up experiment.
        
        Args:
            save_local: Whether to save logs locally
            exit_code: Exit code for the experiment
        """
        if save_local:
            try:
                self.save_local_logs()
            except Exception as e:
                logger.warning(f"Failed to save local logs: {e}")
        
        # Finish W&B run if available
        if self.run is not None:
            try:
                wandb.finish(exit_code=exit_code)
                logger.info("✅ W&B experiment finished")
            except Exception as e:
                logger.warning(f"Failed to finish W&B run: {e}")
        
        self._initialized = False
        self.run = None
        
        logger.info("🏁 Experiment tracking finished")
    
    def get_run_url(self) -> Optional[str]:
        """Get W&B run URL if available."""
        if self.run is not None:
            return self.run.get_url()
        return None
    
    def get_run_id(self) -> Optional[str]:
        """Get W&B run ID if available."""
        if self.run is not None:
            return self.run.id
        return None


class MLExperimentContext:
    """
    Context manager for ML experiments with automatic cleanup.
    """
    
    def __init__(self, 
                 tracker: ExperimentTracker,
                 auto_finish: bool = True):
        """
        Initialize experiment context.
        
        Args:
            tracker: Initialized ExperimentTracker
            auto_finish: Whether to automatically finish experiment on exit
        """
        self.tracker = tracker
        self.auto_finish = auto_finish
        self.exception_occurred = False
    
    def __enter__(self):
        """Enter experiment context."""
        if not self.tracker._initialized:
            self.tracker.init_experiment()
        return self.tracker
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit experiment context with cleanup."""
        if exc_type is not None:
            self.exception_occurred = True
            logger.error(f"Experiment failed with exception: {exc_type.__name__}: {exc_val}")
        
        if self.auto_finish:
            exit_code = 1 if self.exception_occurred else 0
            self.tracker.finish_experiment(exit_code=exit_code)
        
        return False  # Don't suppress exceptions


def create_experiment_tracker(config: Dict[str, Any], 
                            experiment_name: Optional[str] = None) -> ExperimentTracker:
    """
    Factory function to create configured experiment tracker.
    
    Args:
        config: Experiment configuration
        experiment_name: Optional experiment name override
        
    Returns:
        Configured ExperimentTracker instance
    """
    # Extract W&B config
    wandb_config = config.get('wandb', {})
    
    # Create tracker
    tracker = ExperimentTracker(
        project_name=wandb_config.get('project', 'house-price-prediction'),
        entity=wandb_config.get('entity'),
        config=config,
        tags=wandb_config.get('tags', ['ml-pipeline']),
        notes=wandb_config.get('notes'),
        name=experiment_name,
        offline=wandb_config.get('offline', False)
    )
    
    return tracker


if __name__ == "__main__":
    # Example usage
    import time
    logging.basicConfig(level=logging.INFO)
    
    # Sample experiment configuration
    config = {
        'model': {
            'type': 'random_forest',
            'n_estimators': 100,
            'max_depth': 10
        },
        'data': {
            'train_size': 0.8,
            'validation_size': 0.1,
            'test_size': 0.1
        },
        'preprocessing': {
            'normalize': True,
            'handle_missing': 'median'
        }
    }
    
    # Test experiment tracking
    tracker = create_experiment_tracker(config, experiment_name="test_experiment")
    
    with MLExperimentContext(tracker) as exp:
        # Log configuration
        exp.log_config(config['model'], prefix='model')
        exp.log_config(config['data'], prefix='data')
        
        # Simulate training loop
        for epoch in range(3):
            # Simulate metrics
            train_loss = 1.0 - (epoch * 0.2) + np.random.random() * 0.1
            val_loss = 1.1 - (epoch * 0.15) + np.random.random() * 0.1
            
            exp.log_metrics({
                'train_loss': train_loss,
                'val_loss': val_loss,
                'epoch': epoch
            }, step=epoch)
            
            time.sleep(0.1)  # Simulate work
        
        # Log final model results
        exp.log_model_results(
            model_name='random_forest',
            metrics={
                'final_rmse': 0.85,
                'final_mae': 0.72,
                'r2_score': 0.91
            },
            hyperparameters=config['model'],
            feature_importance={
                'bedrooms': 0.25,
                'bathrooms': 0.20,
                'sqft_living': 0.35,
                'location_score': 0.20
            }
        )
    
    print("✅ Example experiment completed!")