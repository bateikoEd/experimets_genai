"""
Model evaluation and metrics calculation utilities.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Comprehensive model evaluation with metrics and visualizations.
    """
    
    def __init__(self, feature_names: Optional[List[str]] = None):
        """
        Initialize evaluator.
        
        Args:
            feature_names: List of feature names for interpretability
        """
        self.feature_names = feature_names
        
    def calculate_regression_metrics(self, 
                                   y_true: np.ndarray, 
                                   y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calculate comprehensive regression metrics.
        
        Args:
            y_true: True target values
            y_pred: Predicted target values
            
        Returns:
            Dictionary with calculated metrics
        """
        # Basic error calculations
        mse = np.mean((y_true - y_pred) ** 2)
        mae = np.mean(np.abs(y_true - y_pred))
        
        # R-squared calculation
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Additional metrics
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1e-8))) * 100
        max_error = np.max(np.abs(y_true - y_pred))
        mean_error = np.mean(y_pred - y_true)
        
        metrics = {
            'RMSE': np.sqrt(mse),
            'MAE': mae,
            'R2': r2,
            'MAPE': mape,
            'Max_Error': max_error,
            'Mean_Error': mean_error,
        }
        
        return metrics
    
    def extract_feature_importance(self, 
                                 model: Any, 
                                 method: str = 'auto') -> Dict[str, float]:
        """
        Extract feature importance from trained model.
        
        Args:
            model: Trained sklearn model
            method: Method to extract importance ('auto', 'coefficients', 'importance')
            
        Returns:
            Dictionary mapping feature names to importance scores
        """
        importance_dict = {}
        
        # Auto-detect method based on model type
        if method == 'auto':
            if hasattr(model, 'feature_importances_'):
                method = 'importance'
            elif hasattr(model, 'coef_'):
                method = 'coefficients'
            else:
                logger.warning("Model does not support feature importance extraction")
                return importance_dict
        
        # Extract importance scores
        if method == 'importance' and hasattr(model, 'feature_importances_'):
            importance_scores = model.feature_importances_
        elif method == 'coefficients' and hasattr(model, 'coef_'):
            importance_scores = np.abs(model.coef_)  # Use absolute values
        else:
            logger.warning(f"Cannot extract importance using method '{method}'")
            return importance_dict
        
        # Create feature names if not provided
        if self.feature_names is None:
            feature_names = [f'feature_{i}' for i in range(len(importance_scores))]
        else:
            feature_names = self.feature_names
        
        # Create dictionary
        for name, score in zip(feature_names, importance_scores):
            importance_dict[name] = float(score)
        
        return importance_dict
    
    def plot_feature_importance(self, 
                              importance_dict: Dict[str, float],
                              top_n: int = 30,
                              title: str = "Feature Importance",
                              figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
        """
        Plot feature importance as horizontal bar chart.
        
        Args:
            importance_dict: Dictionary with feature importance scores
            top_n: Number of top features to display
            title: Plot title
            figsize: Figure size
            
        Returns:
            Matplotlib figure
        """
        # Sort features by importance
        sorted_features = sorted(importance_dict.items(), 
                               key=lambda x: x[1], reverse=True)
        
        # Take top N features
        top_features = sorted_features[:top_n]
        
        if not top_features:
            logger.warning("No features to plot")
            return plt.figure()
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        feature_names = [item[0] for item in top_features]
        importance_scores = [item[1] for item in top_features]
        
        # Create horizontal bar chart
        bars = ax.barh(range(len(feature_names)), importance_scores, 
                      color='skyblue', edgecolor='black', alpha=0.7)
        
        # Customize plot
        ax.set_yticks(range(len(feature_names)))
        ax.set_yticklabels(feature_names)
        ax.set_xlabel('Importance Score')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, score) in enumerate(zip(bars, importance_scores)):
            ax.text(bar.get_width() + 0.001 * max(importance_scores), 
                   bar.get_y() + bar.get_height()/2,
                   f'{score:.4f}', 
                   ha='left', va='center', fontsize=8)
        
        # Invert y-axis to show most important features at top
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        return fig
    
    def plot_prediction_analysis(self, 
                               y_true: np.ndarray, 
                               y_pred: np.ndarray,
                               title: str = "Prediction Analysis") -> plt.Figure:
        """
        Create comprehensive prediction analysis plots.
        
        Args:
            y_true: True target values
            y_pred: Predicted target values
            title: Plot title
            
        Returns:
            Matplotlib figure with subplots
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        # 1. Actual vs Predicted scatter plot
        axes[0, 0].scatter(y_true, y_pred, alpha=0.6, edgecolors='black', s=20)
        
        # Perfect prediction line
        min_val = min(y_true.min(), y_pred.min())
        max_val = max(y_true.max(), y_pred.max())
        axes[0, 0].plot([min_val, max_val], [min_val, max_val], 
                       'r--', linewidth=2, label='Perfect Prediction')
        
        axes[0, 0].set_xlabel('Actual Values')
        axes[0, 0].set_ylabel('Predicted Values')
        axes[0, 0].set_title('Actual vs Predicted')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Add R² annotation
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        axes[0, 0].text(0.05, 0.95, f'R² = {r2:.4f}', 
                       transform=axes[0, 0].transAxes,
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 2. Residuals plot
        residuals = y_pred - y_true
        axes[0, 1].scatter(y_pred, residuals, alpha=0.6, edgecolors='black', s=20)
        axes[0, 1].axhline(y=0, color='red', linestyle='--', linewidth=2)
        axes[0, 1].set_xlabel('Predicted Values')
        axes[0, 1].set_ylabel('Residuals (Predicted - Actual)')
        axes[0, 1].set_title('Residual Plot')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Residuals distribution
        axes[1, 0].hist(residuals, bins=50, alpha=0.7, edgecolor='black')
        axes[1, 0].axvline(residuals.mean(), color='red', linestyle='--', 
                          linewidth=2, label=f'Mean = {residuals.mean():.2f}')
        axes[1, 0].set_xlabel('Residuals')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Residuals Distribution')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Simple normality assessment
        # Q-Q plot equivalent using percentiles
        sorted_residuals = np.sort(residuals)
        n = len(sorted_residuals)
        theoretical_quantiles = np.array([(i - 0.5) / n for i in range(1, n + 1)])
        
        # Convert to standard normal quantiles (approximate)
        normal_quantiles = np.array([self._inverse_normal_cdf(q) for q in theoretical_quantiles])
        
        axes[1, 1].scatter(normal_quantiles, sorted_residuals, alpha=0.6, s=20)
        
        # Perfect normal line
        min_q, max_q = normal_quantiles.min(), normal_quantiles.max()
        std_residuals = np.std(residuals)
        mean_residuals = np.mean(residuals)
        perfect_line = mean_residuals + std_residuals * np.array([min_q, max_q])
        axes[1, 1].plot([min_q, max_q], perfect_line, 'r--', linewidth=2, 
                       label='Perfect Normal')
        
        axes[1, 1].set_xlabel('Theoretical Quantiles')
        axes[1, 1].set_ylabel('Sample Quantiles')
        axes[1, 1].set_title('Q-Q Plot (Residuals Normality)')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return fig
    
    def _inverse_normal_cdf(self, p):
        """Approximate inverse normal CDF using Beasley-Springer-Moro algorithm."""
        if p <= 0 or p >= 1:
            return 0
        
        # Coefficients for approximation
        a = [0, -3.969683028665376e+01, 2.209460984245205e+02, 
             -2.759285104469687e+02, 1.383577518672690e+02, 
             -3.066479806614716e+01, 2.506628277459239e+00]
        
        b = [0, -5.447609879822406e+01, 1.615858368580409e+02,
             -1.556989798598866e+02, 6.680131188771972e+01,
             -1.328068155288572e+01]
        
        c = [0, -7.784894002430293e-03, -3.223964580411365e-01,
             -2.400758277161838e+00, -2.549732539343734e+00,
             4.374664141464968e+00, 2.938163982698783e+00]
        
        d = [0, 7.784695709041462e-03, 3.224671290700398e-01,
             2.445134137142996e+00, 3.754408661907416e+00]
        
        if p > 0.5:
            p = 1 - p
            sign = 1
        else:
            sign = -1
        
        if p < 1e-6:
            return sign * 6
        
        t = np.sqrt(-2 * np.log(p))
        
        if t < 5:
            t = t - 1.6
            numer = (((((a[1] * t + a[2]) * t + a[3]) * t + a[4]) * t + a[5]) * t + a[6])
            denom = ((((b[1] * t + b[2]) * t + b[3]) * t + b[4]) * t + b[5]) * t + 1
        else:
            numer = ((((c[1] * t + c[2]) * t + c[3]) * t + c[4]) * t + c[5]) * t + c[6]
            denom = (((d[1] * t + d[2]) * t + d[3]) * t + d[4]) * t + 1
        
        return sign * (numer / denom)
    
    def create_evaluation_report(self, 
                               models_dict: Dict[str, Any],
                               X_test: np.ndarray,
                               y_test: np.ndarray,
                               output_dir: str = "artifacts/evaluation") -> Dict[str, Any]:
        """
        Create comprehensive evaluation report for multiple models.
        
        Args:
            models_dict: Dictionary mapping model names to trained models
            X_test: Test features
            y_test: Test targets
            output_dir: Directory to save plots and reports
            
        Returns:
            Dictionary with evaluation results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Creating evaluation report for {len(models_dict)} models")
        
        report = {
            'model_metrics': {},
            'feature_importance': {},
            'best_model': None,
            'best_score': float('-inf')
        }
        
        # Evaluate each model
        for model_name, model in models_dict.items():
            logger.info(f"Evaluating {model_name}...")
            
            try:
                # Make predictions
                y_pred = model.predict(X_test)
                
                # Calculate metrics
                metrics = self.calculate_regression_metrics(y_test, y_pred)
                report['model_metrics'][model_name] = metrics
                
                # Extract feature importance if available
                importance = self.extract_feature_importance(model)
                if importance:
                    report['feature_importance'][model_name] = importance
                    
                    # Plot feature importance
                    fig = self.plot_feature_importance(
                        importance, 
                        title=f"{model_name} - Feature Importance"
                    )
                    fig.savefig(output_path / f"{model_name}_feature_importance.png", 
                               dpi=300, bbox_inches='tight')
                    plt.close(fig)
                
                # Create prediction analysis plots
                fig = self.plot_prediction_analysis(
                    y_test, y_pred,
                    title=f"{model_name} - Prediction Analysis"
                )
                fig.savefig(output_path / f"{model_name}_prediction_analysis.png",
                           dpi=300, bbox_inches='tight')
                plt.close(fig)
                
                # Track best model (by R²)
                if metrics['R2'] > report['best_score']:
                    report['best_score'] = metrics['R2']
                    report['best_model'] = model_name
                    
                logger.info(f"  ✅ {model_name}: R² = {metrics['R2']:.4f}, "
                           f"RMSE = {metrics['RMSE']:.2f}")
                
            except Exception as e:
                logger.error(f"Failed to evaluate {model_name}: {e}")
                continue
        
        # Create summary comparison
        self._create_model_comparison_plot(report['model_metrics'], output_path)
        
        # Save report to JSON
        import json
        with open(output_path / "evaluation_report.json", 'w') as f:
            # Convert numpy types for JSON serialization
            json_report = {}
            for key, value in report.items():
                if key == 'model_metrics':
                    json_report[key] = {
                        model: {metric: float(score) for metric, score in metrics.items()}
                        for model, metrics in value.items()
                    }
                elif key == 'feature_importance':
                    json_report[key] = {
                        model: {feat: float(score) for feat, score in importance.items()}
                        for model, importance in value.items()
                    }
                else:
                    json_report[key] = value
            
            json.dump(json_report, f, indent=2)
        
        logger.info(f"📊 Evaluation report saved to: {output_path}")
        logger.info(f"🏆 Best model: {report['best_model']} (R² = {report['best_score']:.4f})")
        
        return report
    
    def _create_model_comparison_plot(self, 
                                    metrics_dict: Dict[str, Dict[str, float]], 
                                    output_path: Path):
        """Create comparison plot for all models."""
        if not metrics_dict:
            return
        
        # Create comparison DataFrame
        df_metrics = pd.DataFrame(metrics_dict).T
        
        # Create comparison plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Model Comparison', fontsize=16, fontweight='bold')
        
        # RMSE comparison
        df_metrics['RMSE'].plot(kind='bar', ax=axes[0, 0], color='lightcoral')
        axes[0, 0].set_title('Root Mean Squared Error (Lower is Better)')
        axes[0, 0].set_ylabel('RMSE')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # R² comparison
        df_metrics['R2'].plot(kind='bar', ax=axes[0, 1], color='lightblue')
        axes[0, 1].set_title('R-squared (Higher is Better)')
        axes[0, 1].set_ylabel('R²')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # MAE comparison
        df_metrics['MAE'].plot(kind='bar', ax=axes[1, 0], color='lightgreen')
        axes[1, 0].set_title('Mean Absolute Error (Lower is Better)')
        axes[1, 0].set_ylabel('MAE')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # MAPE comparison
        df_metrics['MAPE'].plot(kind='bar', ax=axes[1, 1], color='gold')
        axes[1, 1].set_title('Mean Absolute Percentage Error (Lower is Better)')
        axes[1, 1].set_ylabel('MAPE (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_path / "model_comparison.png", dpi=300, bbox_inches='tight')
        plt.close(fig)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Generate sample data
    np.random.seed(42)
    n_samples = 1000
    n_features = 10
    
    X = np.random.randn(n_samples, n_features)
    y = np.sum(X[:, :3], axis=1) + np.random.randn(n_samples) * 0.1
    
    # Simple train/test split
    split_idx = int(0.8 * n_samples)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Train a simple mock model for demonstration
    class MockModel:
        def __init__(self):
            self.coef_ = np.random.randn(n_features)
            
        def fit(self, X, y):
            pass
            
        def predict(self, X):
            return X @ self.coef_
    
    model = MockModel()
    
    # Evaluate model
    evaluator = ModelEvaluator(feature_names=[f'feature_{i}' for i in range(n_features)])
    
    y_pred = model.predict(X_test)
    metrics = evaluator.calculate_regression_metrics(y_test, y_pred)
    
    print("📊 Evaluation Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # Feature importance
    importance = evaluator.extract_feature_importance(model)
    print(f"\n🎯 Top 5 Important Features:")
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    for feat, score in sorted_importance[:5]:
        print(f"  {feat}: {score:.4f}")