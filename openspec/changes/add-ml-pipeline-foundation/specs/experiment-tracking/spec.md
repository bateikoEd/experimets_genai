## ADDED Requirements

### Requirement: Weights & Biases Integration
The system SHALL log experiments to Weights & Biases platform for tracking and comparison.

#### Scenario: Experiment initialization
- **WHEN** model training begins
- **THEN** the system creates W&B run with descriptive name and tags
- **AND** logs system configuration and dataset metadata
- **AND** validates WANDB_API_KEY environment variable

#### Scenario: W&B connection failure
- **WHEN** W&B API is unavailable or authentication fails
- **THEN** the system logs warning and continues with local logging
- **AND** saves experiment data locally for later upload
- **AND** provides clear instructions for W&B setup

### Requirement: Parameter and Metric Logging
The system SHALL comprehensively log all experiment parameters and performance metrics.

#### Scenario: Hyperparameter logging
- **WHEN** model training starts
- **THEN** the system logs all model hyperparameters
- **AND** logs data preprocessing configuration
- **AND** records training/validation split details and random seeds

#### Scenario: Performance metric tracking
- **WHEN** model evaluation completes
- **THEN** the system logs RMSE, MAE, and R² scores
- **AND** tracks training time and memory usage
- **AND** logs cross-validation statistics (mean, std)

### Requirement: Artifact Management
The system SHALL upload model artifacts and visualizations for experiment reproducibility.

#### Scenario: Model artifact upload
- **WHEN** training completes successfully
- **THEN** the system uploads serialized model pipeline to W&B
- **AND** includes preprocessing transformers and feature metadata
- **AND** tags artifacts with model type and performance metrics

#### Scenario: Visualization upload
- **WHEN** generating model analysis plots
- **THEN** the system uploads feature importance plots
- **AND** uploads prediction vs actual scatter plots
- **AND** includes residual analysis visualizations

### Requirement: Experiment Comparison
The system SHALL enable systematic comparison of different model experiments.

#### Scenario: Performance comparison dashboard
- **WHEN** multiple experiments are logged
- **THEN** W&B dashboard displays model comparison table
- **AND** shows metric trends across experiments
- **AND** enables filtering by hyperparameters and tags

#### Scenario: Best model identification
- **WHEN** reviewing experiment results
- **THEN** the system highlights best performing model
- **AND** provides links to associated artifacts
- **AND** displays performance improvement over baseline