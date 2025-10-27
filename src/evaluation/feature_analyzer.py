"""
Advanced feature importance and model explainability tools.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any, Optional, Union
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FeatureAnalyzer:
    """
    Advanced feature importance and explainability analysis tools.
    """
    
    def __init__(self, feature_names: Optional[List[str]] = None):
        """
        Initialize feature analyzer.
        
        Args:
            feature_names: List of feature names for interpretability
        """
        self.feature_names = feature_names
    
    def calculate_permutation_importance(self, 
                                       model: Any,
                                       X: np.ndarray,
                                       y: np.ndarray,
                                       metric: str = 'mse',
                                       n_repeats: int = 5,
                                       random_state: int = 42) -> Dict[str, float]:
        """
        Calculate permutation-based feature importance.
        
        Args:
            model: Trained model with predict method
            X: Feature matrix
            y: Target values
            metric: Evaluation metric ('mse', 'mae', 'r2')
            n_repeats: Number of permutation repeats
            random_state: Random seed
            
        Returns:
            Dictionary mapping feature names to importance scores
        """
        np.random.seed(random_state)
        
        # Get baseline score
        baseline_pred = model.predict(X)
        baseline_score = self._calculate_score(y, baseline_pred, metric)
        
        # Feature names
        if self.feature_names is None:
            feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        else:
            feature_names = self.feature_names
        
        importance_scores = {}
        
        for i, feature_name in enumerate(feature_names):
            scores = []
            
            for _ in range(n_repeats):
                # Create permuted copy
                X_permuted = X.copy()
                
                # Permute feature i
                permutation_indices = np.random.permutation(X.shape[0])
                X_permuted[:, i] = X_permuted[permutation_indices, i]
                
                # Calculate score with permuted feature
                permuted_pred = model.predict(X_permuted)
                permuted_score = self._calculate_score(y, permuted_pred, metric)
                
                # Importance is the drop in performance
                if metric == 'r2':
                    importance = baseline_score - permuted_score  # Higher is better
                else:
                    importance = permuted_score - baseline_score  # Lower is better
                
                scores.append(importance)
            
            # Average importance across repeats
            importance_scores[feature_name] = float(np.mean(scores))
        
        return importance_scores
    
    def _calculate_score(self, y_true: np.ndarray, y_pred: np.ndarray, metric: str) -> float:
        """Calculate evaluation score based on metric."""
        if metric == 'mse':
            return np.mean((y_true - y_pred) ** 2)
        elif metric == 'mae':
            return np.mean(np.abs(y_true - y_pred))
        elif metric == 'r2':
            ss_res = np.sum((y_true - y_pred) ** 2)
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
            return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        else:
            raise ValueError(f"Unsupported metric: {metric}")
    
    def analyze_feature_correlations(self, 
                                   X: np.ndarray, 
                                   feature_names: Optional[List[str]] = None) -> Tuple[np.ndarray, List[str]]:
        """
        Analyze feature correlations to identify multicollinearity.
        
        Args:
            X: Feature matrix
            feature_names: Feature names
            
        Returns:
            Tuple of (correlation matrix, feature names)
        """
        if feature_names is None:
            if self.feature_names is not None:
                feature_names = self.feature_names
            else:
                feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        
        # Calculate correlation matrix
        correlation_matrix = np.corrcoef(X.T)
        
        return correlation_matrix, feature_names
    
    def plot_feature_correlations(self, 
                                X: np.ndarray,
                                feature_names: Optional[List[str]] = None,
                                title: str = "Feature Correlations",
                                figsize: Tuple[int, int] = (12, 10)) -> plt.Figure:
        """
        Plot feature correlation heatmap.
        
        Args:
            X: Feature matrix
            feature_names: Feature names
            title: Plot title
            figsize: Figure size
            
        Returns:
            Matplotlib figure
        """
        corr_matrix, names = self.analyze_feature_correlations(X, feature_names)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create heatmap
        im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Correlation Coefficient', fontsize=12)
        
        # Set ticks and labels
        ax.set_xticks(range(len(names)))
        ax.set_yticks(range(len(names)))
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.set_yticklabels(names)
        
        # Add correlation values as text
        for i in range(len(names)):
            for j in range(len(names)):
                text = ax.text(j, i, f'{corr_matrix[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=8)
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        return fig
    
    def identify_redundant_features(self, 
                                  X: np.ndarray,
                                  threshold: float = 0.95,
                                  feature_names: Optional[List[str]] = None) -> List[Tuple[str, str, float]]:
        """
        Identify highly correlated feature pairs that might be redundant.
        
        Args:
            X: Feature matrix
            threshold: Correlation threshold for identifying redundancy
            feature_names: Feature names
            
        Returns:
            List of tuples (feature1, feature2, correlation)
        """
        corr_matrix, names = self.analyze_feature_correlations(X, feature_names)
        
        redundant_pairs = []
        
        # Check upper triangle of correlation matrix
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if abs(corr_matrix[i, j]) >= threshold:
                    redundant_pairs.append((names[i], names[j], corr_matrix[i, j]))
        
        # Sort by correlation strength
        redundant_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        
        return redundant_pairs
    
    def plot_feature_distributions(self, 
                                 X: np.ndarray,
                                 y: Optional[np.ndarray] = None,
                                 feature_names: Optional[List[str]] = None,
                                 n_cols: int = 4,
                                 figsize: Tuple[int, int] = (16, 12)) -> plt.Figure:
        """
        Plot distributions of features, optionally colored by target.
        
        Args:
            X: Feature matrix
            y: Optional target values for coloring
            feature_names: Feature names
            n_cols: Number of columns in subplot grid
            figsize: Figure size
            
        Returns:
            Matplotlib figure
        """
        if feature_names is None:
            if self.feature_names is not None:
                feature_names = self.feature_names
            else:
                feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        
        n_features = X.shape[1]
        n_rows = (n_features + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        
        # Flatten axes for easy indexing
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        else:
            axes = axes.flatten()
        
        for i in range(n_features):
            ax = axes[i] if n_features > 1 else axes[0]
            
            # Plot histogram
            if y is not None:
                # Create scatter plot colored by target
                ax.scatter(X[:, i], y, alpha=0.6, s=20, c=y, cmap='viridis')
                ax.set_ylabel('Target Value')
                ax.set_xlabel(feature_names[i])
                ax.set_title(f'{feature_names[i]} vs Target')
            else:
                # Simple histogram
                ax.hist(X[:, i], bins=30, alpha=0.7, edgecolor='black')
                ax.set_xlabel(feature_names[i])
                ax.set_ylabel('Frequency')
                ax.set_title(f'Distribution: {feature_names[i]}')
            
            ax.grid(True, alpha=0.3)
        
        # Hide empty subplots
        for i in range(n_features, len(axes)):
            axes[i].set_visible(False)
        
        plt.suptitle('Feature Distributions', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        return fig
    
    def calculate_feature_statistics(self, 
                                   X: np.ndarray,
                                   feature_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Calculate comprehensive statistics for all features.
        
        Args:
            X: Feature matrix
            feature_names: Feature names
            
        Returns:
            DataFrame with feature statistics
        """
        if feature_names is None:
            if self.feature_names is not None:
                feature_names = self.feature_names
            else:
                feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        
        stats = []
        
        for i, name in enumerate(feature_names):
            feature_data = X[:, i]
            
            feature_stats = {
                'Feature': name,
                'Count': len(feature_data),
                'Mean': np.mean(feature_data),
                'Std': np.std(feature_data),
                'Min': np.min(feature_data),
                'Q1': np.percentile(feature_data, 25),
                'Median': np.percentile(feature_data, 50),
                'Q3': np.percentile(feature_data, 75),
                'Max': np.max(feature_data),
                'IQR': np.percentile(feature_data, 75) - np.percentile(feature_data, 25),
                'Skewness': self._calculate_skewness(feature_data),
                'Kurtosis': self._calculate_kurtosis(feature_data),
                'Missing': np.sum(np.isnan(feature_data)) if feature_data.dtype.kind in 'fc' else 0,
                'Unique': len(np.unique(feature_data)),
            }
            
            stats.append(feature_stats)
        
        return pd.DataFrame(stats)
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of data."""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 3)
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of data."""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 4) - 3
    
    def create_feature_importance_report(self, 
                                       model: Any,
                                       X: np.ndarray,
                                       y: np.ndarray,
                                       feature_names: Optional[List[str]] = None,
                                       output_dir: str = "artifacts/feature_analysis") -> Dict[str, Any]:
        """
        Create comprehensive feature importance and analysis report.
        
        Args:
            model: Trained model
            X: Feature matrix
            y: Target values
            feature_names: Feature names
            output_dir: Output directory for plots and reports
            
        Returns:
            Dictionary with analysis results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if feature_names is not None:
            self.feature_names = feature_names
        
        logger.info("Creating comprehensive feature analysis report...")
        
        report = {}
        
        # 1. Model-based feature importance
        if hasattr(model, 'feature_importances_') or hasattr(model, 'coef_'):
            from ..evaluation.evaluator import ModelEvaluator
            evaluator = ModelEvaluator(feature_names=self.feature_names)
            
            model_importance = evaluator.extract_feature_importance(model)
            report['model_importance'] = model_importance
            
            # Plot model importance
            if model_importance:
                fig = evaluator.plot_feature_importance(
                    model_importance,
                    title="Model-Based Feature Importance"
                )
                fig.savefig(output_path / "model_feature_importance.png", 
                           dpi=300, bbox_inches='tight')
                plt.close(fig)
        
        # 2. Permutation importance
        logger.info("Calculating permutation importance...")
        perm_importance = self.calculate_permutation_importance(model, X, y)
        report['permutation_importance'] = perm_importance
        
        # Plot permutation importance
        fig = self._plot_importance_dict(
            perm_importance,
            title="Permutation Feature Importance"
        )
        fig.savefig(output_path / "permutation_feature_importance.png", 
                   dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # 3. Feature correlations
        logger.info("Analyzing feature correlations...")
        fig = self.plot_feature_correlations(X, title="Feature Correlation Matrix")
        fig.savefig(output_path / "feature_correlations.png", 
                   dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # 4. Redundant features
        redundant_features = self.identify_redundant_features(X)
        report['redundant_features'] = redundant_features
        
        # 5. Feature distributions
        logger.info("Creating feature distribution plots...")
        fig = self.plot_feature_distributions(X, y)
        fig.savefig(output_path / "feature_distributions.png", 
                   dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        # 6. Feature statistics
        feature_stats = self.calculate_feature_statistics(X)
        report['feature_statistics'] = feature_stats
        
        # Save statistics to CSV
        feature_stats.to_csv(output_path / "feature_statistics.csv", index=False)
        
        # 7. Create summary comparison plot
        if model_importance and perm_importance:
            self._create_importance_comparison_plot(
                model_importance, perm_importance, output_path
            )
        
        # Save report
        import json
        json_report = {}
        for key, value in report.items():
            if key == 'feature_statistics':
                json_report[key] = value.to_dict('records')
            elif key in ['model_importance', 'permutation_importance']:
                json_report[key] = {k: float(v) for k, v in value.items()}
            elif key == 'redundant_features':
                json_report[key] = [(f1, f2, float(corr)) for f1, f2, corr in value]
            else:
                json_report[key] = value
        
        with open(output_path / "feature_analysis_report.json", 'w') as f:
            json.dump(json_report, f, indent=2)
        
        logger.info(f"📊 Feature analysis report saved to: {output_path}")
        
        if redundant_features:
            logger.info(f"⚠️  Found {len(redundant_features)} highly correlated feature pairs")
            for f1, f2, corr in redundant_features[:3]:  # Show top 3
                logger.info(f"   {f1} ↔ {f2}: {corr:.3f}")
        
        return report
    
    def _plot_importance_dict(self, 
                            importance_dict: Dict[str, float],
                            title: str = "Feature Importance",
                            top_n: int = 30,
                            figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
        """Plot importance dictionary as horizontal bar chart."""
        # Sort features by importance
        sorted_features = sorted(importance_dict.items(), 
                               key=lambda x: abs(x[1]), reverse=True)
        
        # Take top N features
        top_features = sorted_features[:top_n]
        
        if not top_features:
            return plt.figure()
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        feature_names = [item[0] for item in top_features]
        importance_scores = [item[1] for item in top_features]
        
        # Color bars by positive/negative importance
        colors = ['red' if score < 0 else 'skyblue' for score in importance_scores]
        
        # Create horizontal bar chart
        bars = ax.barh(range(len(feature_names)), importance_scores, 
                      color=colors, edgecolor='black', alpha=0.7)
        
        # Customize plot
        ax.set_yticks(range(len(feature_names)))
        ax.set_yticklabels(feature_names)
        ax.set_xlabel('Importance Score')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3)
        ax.axvline(x=0, color='black', linewidth=1, alpha=0.5)
        
        # Add value labels on bars
        max_abs_score = max(abs(s) for s in importance_scores) if importance_scores else 1
        for i, (bar, score) in enumerate(zip(bars, importance_scores)):
            label_x = bar.get_width() + 0.01 * max_abs_score if score >= 0 else bar.get_width() - 0.01 * max_abs_score
            ax.text(label_x, bar.get_y() + bar.get_height()/2,
                   f'{score:.4f}', 
                   ha='left' if score >= 0 else 'right', va='center', fontsize=8)
        
        # Invert y-axis to show most important features at top
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        return fig
    
    def _create_importance_comparison_plot(self, 
                                         model_importance: Dict[str, float],
                                         perm_importance: Dict[str, float],
                                         output_path: Path):
        """Create comparison plot between model and permutation importance."""
        # Find common features
        common_features = set(model_importance.keys()) & set(perm_importance.keys())
        
        if not common_features:
            return
        
        model_scores = [model_importance[f] for f in common_features]
        perm_scores = [perm_importance[f] for f in common_features]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Scatter plot
        ax.scatter(model_scores, perm_scores, alpha=0.7, s=50)
        
        # Add feature labels for interesting points
        for i, feature in enumerate(common_features):
            if abs(model_scores[i]) > 0.05 or abs(perm_scores[i]) > 0.05:
                ax.annotate(feature, (model_scores[i], perm_scores[i]), 
                           xytext=(5, 5), textcoords='offset points', 
                           fontsize=8, alpha=0.8)
        
        # Perfect correlation line
        min_val = min(min(model_scores), min(perm_scores))
        max_val = max(max(model_scores), max(perm_scores))
        ax.plot([min_val, max_val], [min_val, max_val], 
               'r--', alpha=0.7, label='Perfect Agreement')
        
        ax.set_xlabel('Model-Based Importance')
        ax.set_ylabel('Permutation Importance')
        ax.set_title('Feature Importance Comparison')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_path / "importance_comparison.png", dpi=300, bbox_inches='tight')
        plt.close(fig)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Generate sample data
    np.random.seed(42)
    n_samples = 1000
    n_features = 10
    
    X = np.random.randn(n_samples, n_features)
    # Make some features correlated
    X[:, 1] = X[:, 0] + 0.1 * np.random.randn(n_samples)  # Highly correlated
    X[:, 2] = 0.5 * X[:, 0] + 0.5 * X[:, 3] + 0.1 * np.random.randn(n_samples)
    
    y = np.sum(X[:, :3], axis=1) + np.random.randn(n_samples) * 0.1
    
    # Simple mock model
    class MockModel:
        def __init__(self):
            self.feature_importances_ = np.abs(np.random.randn(n_features))
            
        def predict(self, X):
            return np.sum(X * self.feature_importances_, axis=1)
    
    model = MockModel()
    
    # Analyze features
    feature_names = [f'feature_{i}' for i in range(n_features)]
    analyzer = FeatureAnalyzer(feature_names=feature_names)
    
    # Test permutation importance
    perm_importance = analyzer.calculate_permutation_importance(model, X, y)
    print("🔍 Permutation Importance:")
    for feat, score in sorted(perm_importance.items(), key=lambda x: abs(x[1]), reverse=True)[:5]:
        print(f"  {feat}: {score:.4f}")
    
    # Test redundant features
    redundant = analyzer.identify_redundant_features(X, threshold=0.8)
    print(f"\n⚠️  Redundant Features (>{0.8:.1f} correlation):")
    for f1, f2, corr in redundant:
        print(f"  {f1} ↔ {f2}: {corr:.3f}")
    
    # Feature statistics
    stats = analyzer.calculate_feature_statistics(X)
    print(f"\n📊 Feature Statistics:")
    print(stats[['Feature', 'Mean', 'Std', 'Skewness']].head())