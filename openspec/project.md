# Project Context

## Purpose
This project is focused on building a comprehensive **machine learning pipeline for house price prediction**. The main objectives are:
- Perform exploratory data analysis (EDA) on real estate data
- Build robust ML models for property price prediction
- Create a production-ready pipeline with experiment tracking
- Develop CLI tools for real-time inference
- Integrate with Databricks for scalable data processing

## Tech Stack
- **Python 3.11** - Primary programming language
- **Databricks** - Cloud platform for data processing and ML workflows
- **Jupyter Notebooks** - Interactive development and EDA
- **Weights & Biases (W&B)** - Experiment tracking and model monitoring
- **scikit-learn** - Machine learning algorithms and preprocessing
- **NLTK & spaCy** - Natural language processing for text features
- **PySpark** (optional) - Scalable data processing
- **pandas & numpy** - Data manipulation and numerical computing
- **matplotlib & seaborn** - Data visualization
- **joblib** - Model serialization and persistence

## Project Conventions

### Code Style
- Follow **PEP 8** Python style guidelines
- Use descriptive variable names (e.g., `carpet_area`, `property_status`)
- Prefer snake_case for variables and functions
- Use type hints where appropriate
- Document functions and classes with docstrings

### Architecture Patterns
- **Pipeline-based architecture** using scikit-learn's Pipeline and ColumnTransformer
- **Modular preprocessing** with separate transforms for numeric, categorical, and text features
- **Experiment tracking** with structured logging to W&B
- **CLI interface** for model inference and deployment
- **Configuration-driven** approach using environment variables (e.g., `WANDB_API_KEY`, `TARGET_COL`)

### Testing Strategy
- Validate data schema and feature engineering pipelines
- Test model performance with regression metrics (RMSE, MAE, R²)
- Cross-validation for model selection and hyperparameter tuning
- Integration tests for CLI inference functionality

### Git Workflow
- Use **feature branches** for development (e.g., `feature/databricks-copilot`)
- Main branch: `master`
- Commit messages should be descriptive and follow conventional commit format
- Use meaningful branch names that describe the feature being developed

## Domain Context
**Real Estate & Property Valuation:**
- Working with residential property data (houses and flats)
- Key features include: carpet area, furnishing status, location, amenities
- Target variable: `total_amount` (property price)
- Text features: property descriptions, location names, titles
- Categorical features: furnishing type, property status, facing direction
- Numerical features: area measurements, room counts, floor numbers

**Machine Learning Pipeline:**
- Multi-modal feature processing (numerical, categorical, textual)
- Regression problem with continuous target (price)
- Feature importance analysis for model interpretability
- Production deployment considerations with CLI interface

## Important Constraints
- Large dataset (house_prices.csv > 50MB) requires efficient memory management
- Text processing needs to handle various languages and formats in descriptions
- Model must be serializable and deployable via CLI
- Performance requirements for real-time inference
- Integration with Databricks cloud environment

## External Dependencies
- **Databricks Workspace** - `https://dbc-5fa3019d-0508.cloud.databricks.com`
- **Weights & Biases** - Experiment tracking platform (requires API key)
- **databricks-connect** - Local development integration with Databricks
- **NLTK data** - Language models and corpora for text processing
- **spaCy models** - Pre-trained NLP models for NER and tokenization
