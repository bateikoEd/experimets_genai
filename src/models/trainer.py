"""
Model training framework for house price prediction.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.model_selection import cross_val_score, GridSearchCV, train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
import logging
from typing import Dict, List, Tuple, Any, Optional
import time
from dataclasses import dataclass
import joblib

logger = logging.getLogger(__name__)


@dataclass
class ModelResult:
    """Container for model training results."""
    name: str
    model: Any
    cv_scores: np.ndarray
    cv_mean: float
    cv_std: float
    training_time: float
    best_params: Optional[Dict] = None
    test_score: Optional[float] = None


class ModelTrainer:
    """
    Comprehensive model training framework for regression tasks.
    
    Supports multiple algorithms with hyperparameter tuning and cross-validation.
    """
    
    def __init__(self, 
                 cv_folds: int = 5,
                 random_state: int = 42,
                 scoring: str = 'neg_mean_squared_error',
                 n_jobs: int = -1):
        """
        Initialize model trainer.
        
        Args:
            cv_folds: Number of cross-validation folds
            random_state: Random state for reproducibility
            scoring: Scoring metric for cross-validation
            n_jobs: Number of parallel jobs (-1 uses all processors)
        """
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.scoring = scoring
        self.n_jobs = n_jobs
        
        # Will be set during training
        self.results = {}
        self.best_model = None
        self.best_score = float('-inf')
        
    def get_model_configs(self) -> Dict[str, Dict]:
        """
        Get model configurations with hyperparameter grids.
        
        Returns:
            Dictionary mapping model names to configurations
        """
        configs = {
            'linear_regression': {
                'model': LinearRegression(),
                'params': {}  # No hyperparameters to tune
            },
            
            'ridge': {
                'model': Ridge(random_state=self.random_state),
                'params': {
                    'alpha': [0.1, 1.0, 10.0, 100.0, 1000.0]
                }
            },
            
            'lasso': {
                'model': Lasso(random_state=self.random_state, max_iter=2000),
                'params': {
                    'alpha': [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
                }
            },
            
            'random_forest': {
                'model': RandomForestRegressor(
                    random_state=self.random_state,
                    n_jobs=self.n_jobs
                ),
                'params': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, None],
                    'min_samples_split': [2, 5],
                    'min_samples_leaf': [1, 2]
                }
            },
            
            'extra_trees': {
                'model': ExtraTreesRegressor(
                    random_state=self.random_state,
                    n_jobs=self.n_jobs
                ),
                'params': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, None],
                    'min_samples_split': [2, 5],
                    'min_samples_leaf': [1, 2]
                }
            }
        }
        
        return configs
    
    def train_single_model(self, 
                          name: str, 
                          model: Any, 
                          param_grid: Dict,
                          X_train: np.ndarray, 
                          y_train: np.ndarray) -> ModelResult:
        """
        Train a single model with hyperparameter tuning.
        
        Args:
            name: Model name
            model: Sklearn model instance
            param_grid: Hyperparameter grid for tuning
            X_train: Training features
            y_train: Training targets
            
        Returns:
            ModelResult with training results
        """
        logger.info(f"Training {name}...")
        start_time = time.time()
        
        if param_grid:
            # Hyperparameter tuning with GridSearchCV
            grid_search = GridSearchCV(
                model,
                param_grid,
                cv=self.cv_folds,
                scoring=self.scoring,
                n_jobs=self.n_jobs,
                verbose=0
            )
            
            grid_search.fit(X_train, y_train)
            
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            cv_scores = cross_val_score(
                best_model, X_train, y_train, 
                cv=self.cv_folds, scoring=self.scoring, n_jobs=self.n_jobs
            )
            
        else:
            # No hyperparameters to tune
            model.fit(X_train, y_train)
            best_model = model
            best_params = None
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=self.cv_folds, scoring=self.scoring, n_jobs=self.n_jobs
            )
        
        training_time = time.time() - start_time
        
        # Convert negative MSE scores to positive RMSE for interpretability
        if self.scoring == 'neg_mean_squared_error':
            cv_scores = np.sqrt(-cv_scores)
        
        result = ModelResult(
            name=name,
            model=best_model,
            cv_scores=cv_scores,
            cv_mean=cv_scores.mean(),
            cv_std=cv_scores.std(),
            training_time=training_time,
            best_params=best_params
        )
        
        logger.info(f"  ✅ {name}: CV RMSE = {result.cv_mean:.2f} ± {result.cv_std:.2f}")
        if best_params:
            logger.info(f"     Best params: {best_params}")
        
        return result
    
    def train_all_models(self, 
                        X_train: np.ndarray, 
                        y_train: np.ndarray,
                        X_test: Optional[np.ndarray] = None,
                        y_test: Optional[np.ndarray] = None) -> Dict[str, ModelResult]:
        """
        Train all configured models.
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_test: Optional test features for final evaluation
            y_test: Optional test targets for final evaluation
            
        Returns:
            Dictionary mapping model names to results
        """
        logger.info(f"Starting model training with {self.cv_folds}-fold CV")
        logger.info(f"Training set size: {X_train.shape}")
        if X_test is not None:
            logger.info(f"Test set size: {X_test.shape}")
        
        configs = self.get_model_configs()
        self.results = {}
        
        # Train each model
        for name, config in configs.items():
            try:
                result = self.train_single_model(
                    name=name,
                    model=config['model'],
                    param_grid=config['params'],
                    X_train=X_train,
                    y_train=y_train
                )
                
                # Evaluate on test set if provided
                if X_test is not None and y_test is not None:
                    y_pred = result.model.predict(X_test)
                    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                    result.test_score = test_rmse
                    logger.info(f"     Test RMSE: {test_rmse:.2f}")
                
                self.results[name] = result
                
                # Track best model
                if result.cv_mean > self.best_score:  # Higher is better for R²
                    self.best_score = result.cv_mean
                    self.best_model = result.model
                
            except Exception as e:
                logger.error(f"Failed to train {name}: {e}")
                continue
        
        # Select best model (lowest CV RMSE)
        if self.results:
            best_name = min(self.results.keys(), 
                           key=lambda x: self.results[x].cv_mean)
            self.best_model = self.results[best_name].model
            logger.info(f"\n🏆 Best model: {best_name} "
                       f"(CV RMSE: {self.results[best_name].cv_mean:.2f})")
        
        return self.results
    
    def get_results_summary(self) -> pd.DataFrame:
        """
        Get training results as a summary DataFrame.
        
        Returns:
            DataFrame with model comparison
        """
        if not self.results:
            return pd.DataFrame()
        
        summary_data = []
        for name, result in self.results.items():
            summary_data.append({
                'Model': name,
                'CV_RMSE_Mean': result.cv_mean,
                'CV_RMSE_Std': result.cv_std,
                'Training_Time_Sec': result.training_time,
                'Test_RMSE': result.test_score if result.test_score else None,
                'Best_Params': str(result.best_params) if result.best_params else 'None'
            })
        
        df = pd.DataFrame(summary_data)
        return df.sort_values('CV_RMSE_Mean').reset_index(drop=True)
    
    def calculate_detailed_metrics(self, 
                                 X_test: np.ndarray, 
                                 y_test: np.ndarray) -> Dict[str, Dict[str, float]]:
        """
        Calculate detailed metrics for all trained models on test set.
        
        Args:
            X_test: Test features
            y_test: Test targets
            
        Returns:
            Dictionary mapping model names to metric dictionaries
        """
        detailed_metrics = {}
        
        for name, result in self.results.items():
            try:
                y_pred = result.model.predict(X_test)
                
                metrics = {
                    'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)),
                    'MAE': mean_absolute_error(y_test, y_pred),
                    'R2': r2_score(y_test, y_pred)
                }
                
                detailed_metrics[name] = metrics
                
            except Exception as e:
                logger.error(f"Failed to calculate metrics for {name}: {e}")
                detailed_metrics[name] = {'RMSE': None, 'MAE': None, 'R2': None}
        
        return detailed_metrics
    
    def save_best_model(self, filepath: str):
        """
        Save the best model to file.
        
        Args:
            filepath: Path to save the model
        """
        if self.best_model is None:
            raise ValueError("No models have been trained yet")
        
        joblib.dump(self.best_model, filepath)
        logger.info(f"Best model saved to: {filepath}")
    
    def load_model(self, filepath: str):
        """
        Load a model from file.
        
        Args:
            filepath: Path to the saved model
        """
        self.best_model = joblib.load(filepath)
        logger.info(f"Model loaded from: {filepath}")
        
        return self.best_model


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Generate sample data
    np.random.seed(42)
    n_samples = 1000
    n_features = 10
    
    X = np.random.randn(n_samples, n_features)
    y = np.sum(X[:, :3], axis=1) + np.random.randn(n_samples) * 0.1
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train models
    trainer = ModelTrainer(cv_folds=5)
    results = trainer.train_all_models(X_train, y_train, X_test, y_test)
    
    # Display results
    print("\n📊 Model Comparison:")
    summary = trainer.get_results_summary()
    print(summary)
    
    # Detailed metrics
    print("\n📈 Detailed Test Metrics:")
    detailed_metrics = trainer.calculate_detailed_metrics(X_test, y_test)
    for name, metrics in detailed_metrics.items():
        print(f"{name}: RMSE={metrics['RMSE']:.4f}, "
              f"MAE={metrics['MAE']:.4f}, R²={metrics['R2']:.4f}")