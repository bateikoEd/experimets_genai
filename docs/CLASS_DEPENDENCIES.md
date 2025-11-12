# Class & Object Dependencies

This document lists the main classes in `src/`, describes their responsibilities and relationships, and includes a Mermaid `classDiagram` you can preview.

## Key classes (file -> class -> short purpose)

- `src/config/wandb_config.py` -> `WandBConfig`
  - Manage Weights & Biases runs, logging metrics and artifacts. A default `wandb_config` instance is created in the module.

- `src/data_processing/data_loader.py` -> `DataValidator`
  - Validate DataFrame schema, detect missing/unexpected columns and data quality checks.

- `src/data_processing/numeric_preprocessing.py` -> `NumericPreprocessor`
  - Scikit-learn transformer for numeric imputation, scaling, and outlier handling.

- `src/data_processing/categorical_preprocessing.py` -> `CategoricalPreprocessor`, `RareCategoryHandler`
  - Transformers for categorical imputation, rare category grouping, and one-hot encoding.

- `src/data_processing/text_preprocessing.py` -> `TextPreprocessor`
  - TF-IDF vectorization and optional spaCy NER feature extraction for text columns.

- `src/data_processing/unified_pipeline.py` -> `UnifiedPreprocessor`
  - Composes numeric/categorical/text preprocessors into a single `ColumnTransformer`. Exposes `get_feature_names_out()` and feature mapping helpers.

- `src/models/trainer.py` -> `ModelResult`, `ModelTrainer`
  - Training orchestration, hyperparameter search (GridSearchCV), CV evaluation, returns `ModelResult` dataclass instances.

- `src/models/persistence.py` -> `ModelPersistence`, `ModelPredictor`
  - Save/load model packages (model + preprocessor + metadata). `ModelPredictor` is a convenience wrapper around loaded models.

- `src/evaluation/evaluator.py` -> `ModelEvaluator`
  - Metrics calculation, extraction of feature importance (coef_/feature_importances_), and plotting utilities.

- `src/evaluation/feature_analyzer.py` -> `FeatureAnalyzer`
  - Permutation importance, correlation analysis, distribution plots; uses `ModelEvaluator` for model-based importance.

- `src/experiment_tracking/enhanced_trainer.py` -> `ExperimentModelTrainer`
  - Extends `ModelTrainer` to log configs/metrics/artifacts to `ExperimentTracker`.

- `src/experiment_tracking/__init__.py` -> `ExperimentTracker`, `MLExperimentContext`, `create_experiment_tracker()`
  - Integrates with W&B (or local fallback) to log configs, metrics, tables, artifacts, and manage experiment lifecycle.

## Relationship summary

- Inheritance:
  - Many preprocessors inherit scikit-learn `BaseEstimator` and `TransformerMixin` (e.g. `NumericPreprocessor`, `CategoricalPreprocessor`, `TextPreprocessor`, `RareCategoryHandler`, `UnifiedPreprocessor`).
  - `ExperimentModelTrainer` subclasses `ModelTrainer`.

- Composition / usage:
  - `UnifiedPreprocessor` composes: `NumericPreprocessor`, `CategoricalPreprocessor`, `TextPreprocessor`.
  - `ModelTrainer` produces `ModelResult` objects and uses scikit-learn estimators.
  - `ExperimentModelTrainer` uses `ExperimentTracker`, `ModelPersistence`, and `ModelEvaluator` for logging/reporting.
  - `ModelPersistence` is used by `ModelPredictor` and training/reporting code to save/load models and metadata.
  - `FeatureAnalyzer` uses `ModelEvaluator` to extract model-based importance and plotting helpers.
  - `ExperimentTracker` wraps W&B (if available) and is used by enhanced trainer and ML experiment context.

## Mermaid class diagram

Paste the block below into a Mermaid renderer to visualize the classes and relationships.

```mermaid
classDiagram
  class WandBConfig {
    <<module>> src/config/wandb_config.py
    +initialize_run()
    +log_metrics()
    +log_artifact()
    +finish_run()
  }

  class DataValidator {
    <<module>> src/data_processing/data_loader.py
    +validate_schema()
    +_infer_column_type()
  }

  class NumericPreprocessor {
    <<module>> src/data_processing/numeric_preprocessing.py
    +fit()
    +transform()
  }

  class CategoricalPreprocessor {
    <<module>> src/data_processing/categorical_preprocessing.py
    +fit()
    +transform()
  }

  class RareCategoryHandler {
    <<module>> src/data_processing/categorical_preprocessing.py
    +fit()
    +transform()
  }

  class TextPreprocessor {
    <<module>> src/data_processing/text_preprocessing.py
    +fit()
    +transform()
  }

  class UnifiedPreprocessor {
    <<module>> src/data_processing/unified_pipeline.py
    +fit()
    +transform()
    +get_feature_names_out()
  }

  class ModelResult {
    <<dataclass>> src/models/trainer.py
    name
    model
    cv_scores
  }

  class ModelTrainer {
    <<module>> src/models/trainer.py
    +train_single_model()
    +train_all_models()
    +save_best_model()
  }

  class ModelPersistence {
    <<module>> src/models/persistence.py
    +save_model()
    +load_model()
    +save_training_results()
  }

  class ModelPredictor {
    <<module>> src/models/persistence.py
    +predict()
    +predict_with_confidence()
  }

  class FeatureAnalyzer {
    <<module>> src/evaluation/feature_analyzer.py
    +calculate_permutation_importance()
    +create_feature_importance_report()
  }

  class ModelEvaluator {
    <<module>> src/evaluation/evaluator.py
    +calculate_regression_metrics()
    +extract_feature_importance()
    +plot_feature_importance()
  }

  class ExperimentModelTrainer {
    <<module>> src/experiment_tracking/enhanced_trainer.py
    +train_all_models()
    +create_training_report()
  }

  class ExperimentTracker {
    <<module>> src/experiment_tracking/__init__.py
    +init_experiment()
    +log_metrics()
    +log_model_results()
    +log_artifact()
  }

  class MLExperimentContext {
    <<module>> src/experiment_tracking/__init__.py
    +__enter__()
    +__exit__()
  }

  %% mixins (sketched)
  class BaseEstimator
  class TransformerMixin

  BaseEstimator <|-- NumericPreprocessor
  TransformerMixin <|-- NumericPreprocessor

  BaseEstimator <|-- CategoricalPreprocessor
  TransformerMixin <|-- CategoricalPreprocessor

  BaseEstimator <|-- RareCategoryHandler
  TransformerMixin <|-- RareCategoryHandler

  BaseEstimator <|-- TextPreprocessor
  TransformerMixin <|-- TextPreprocessor

  BaseEstimator <|-- UnifiedPreprocessor
  TransformerMixin <|-- UnifiedPreprocessor

  ModelTrainer <|-- ExperimentModelTrainer

  %% Composition
  UnifiedPreprocessor --> NumericPreprocessor : composes
  UnifiedPreprocessor --> CategoricalPreprocessor : composes
  UnifiedPreprocessor --> TextPreprocessor : composes

  ModelTrainer --> ModelResult : produces
  ExperimentModelTrainer --> ExperimentTracker : logs to
  ExperimentModelTrainer --> ModelPersistence : saves models
  ExperimentModelTrainer --> ModelEvaluator : uses for reports

  ModelPersistence ..> ModelPredictor : used by
  ModelPredictor --> ModelPersistence : calls load_model

  FeatureAnalyzer --> ModelEvaluator : uses
  ModelEvaluator ..> FeatureAnalyzer : used by

  ExperimentTracker ..> "wandb (external)" : integrates

  note for UnifiedPreprocessor "Builds ColumnTransformer and maps output features"
  note for ModelPersistence "Saves model+preprocessor+metadata"
```

---

## How to preview
- In VS Code: open the `.md` file and use the Mermaid preview (if you have the Mermaid extension) or use the built-in Markdown preview on GitHub (GitHub renders Mermaid in PRs and some markdown views).
- Use Mermaid Live Editor: https://mermaid.live and paste the code block.

---

If you'd like, I can also:
- Auto-generate a `docs/` PNG/SVG rendering of the diagrams (requires a local renderer or online service).
- Add method signatures and attributes for each class into the doc (more detailed API reference).
- Create a single `docs/API.md` that documents module functions and public interfaces.

Tell me which extra option you want next and I'll implement it.