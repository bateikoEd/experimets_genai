"""
Weights & Biases configuration and utilities for experiment tracking.
"""

import os
import wandb
from typing import Dict, Any, Optional
from datetime import datetime


class WandBConfig:
    """Configuration manager for Weights & Biases integration."""
    
    def __init__(self, project_name: str = None, entity: str = None):
        """
        Initialize W&B configuration.
        
        Args:
            project_name: W&B project name (defaults to env var or 'house-price-prediction')
            entity: W&B entity/team name (defaults to env var)
        """
        self.project_name = project_name or os.getenv('WANDB_PROJECT', 'house-price-prediction')
        self.entity = entity or os.getenv('WANDB_ENTITY')
        self.api_key = os.getenv('WANDB_API_KEY')
        
    def initialize_run(self, run_name: str = None, config: Dict[str, Any] = None, 
                      tags: list = None) -> Optional[wandb.run]:
        """
        Initialize a W&B run with proper configuration.
        
        Args:
            run_name: Custom run name (auto-generated if None)
            config: Configuration dictionary to log
            tags: List of tags for the run
            
        Returns:
            W&B run object or None if initialization fails
        """
        try:
            if not self.api_key:
                print("Warning: WANDB_API_KEY not found. Logging locally only.")
                wandb.init(mode="offline", project=self.project_name)
                return wandb.run
                
            run_name = run_name or f"house-price-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            run = wandb.init(
                project=self.project_name,
                entity=self.entity,
                name=run_name,
                config=config or {},
                tags=tags or [],
                reinit=True
            )
            
            return run
            
        except Exception as e:
            print(f"Warning: Failed to initialize W&B: {e}")
            print("Continuing with local logging only.")
            return None
    
    def log_metrics(self, metrics: Dict[str, float], step: int = None):
        """Log metrics to W&B if available."""
        try:
            wandb.log(metrics, step=step)
        except Exception as e:
            print(f"Warning: Failed to log metrics to W&B: {e}")
    
    def log_artifact(self, file_path: str, artifact_name: str = None, 
                    artifact_type: str = "model"):
        """Log an artifact to W&B if available."""
        try:
            artifact_name = artifact_name or os.path.basename(file_path)
            artifact = wandb.Artifact(artifact_name, type=artifact_type)
            artifact.add_file(file_path)
            wandb.log_artifact(artifact)
        except Exception as e:
            print(f"Warning: Failed to log artifact to W&B: {e}")
    
    def finish_run(self):
        """Finish the current W&B run."""
        try:
            wandb.finish()
        except Exception as e:
            print(f"Warning: Failed to finish W&B run: {e}")


# Default W&B configuration instance
wandb_config = WandBConfig()