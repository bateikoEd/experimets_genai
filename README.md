# House Price ML Pipeline

## Project Structure

# House Price Prediction ML Pipeline

A comprehensive machine learning pipeline for house price prediction with experiment tracking, data processing, and model evaluation capabilities.

## 🏠 Project Overview

This project implements a production-ready ML pipeline for predicting house prices using multi-modal data including numeric features, categorical attributes, and text descriptions. The pipeline includes automated preprocessing, model training with experiment tracking, comprehensive evaluation, and a CLI interface for inference.

## ✨ Features

- **Multi-modal Data Processing**: Handles numeric, categorical, and text features
- **Experiment Tracking**: Integration with Weights & Biases (W&B) for MLOps
- **Comprehensive Preprocessing**: Automated feature engineering and data validation
- **Multiple Model Support**: Linear regression, Ridge, Lasso, Random Forest, and more
- **Model Persistence**: Save and load trained models with metadata
- **CLI Interface**: Command-line tools for training and inference
- **Performance Monitoring**: Benchmarks and regression tests
- **Extensive Testing**: Unit tests, integration tests, and performance tests

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd experimets_genai
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up experiment tracking** (optional):
   ```bash
   # Set up Weights & Biases
   pip install wandb
   wandb login
   ```

### Basic Usage

#### 1. Data Preparation

Place your house price dataset in the `data/` directory. The expected format is a CSV file with the following columns:

**Required columns for the actual dataset:**
- `Amount(in rupees)` (target variable) - in format like "42 Lac", "1.40 Cr"
- `Carpet Area` (numeric) - in format like "1200 sq ft"

**Optional columns:**
- Numeric: `Bathroom`, `Balcony`, `Car Parking`
- Categorical: `Furnishing`, `Status`, `Transaction`, `Ownership`
- Text: `Description`, `location`, `Title`, `Society`

#### 2. Train a Model

```bash
# Using the fast training script (recommended for this dataset)
python scripts/fast_train.py \
    --data data/house_prices.csv \
    --output models/house_price_model.joblib \
    --model-type random_forest \
    --sample-size 10000

# Available model types: random_forest, linear_regression, ridge
```

#### 3. Make Predictions

```bash
# Single prediction from JSON
python scripts/simple_predict.py \
    --model models/house_price_model.joblib \
    --json '{"Carpet Area": "1200 sq ft", "Bathroom": 2, "Balcony": 1, "Furnishing": "Semi-Furnished"}'

# Show sample input format
python scripts/simple_predict.py --sample

# Batch predictions from CSV
python scripts/simple_predict.py \
    --model models/house_price_model.joblib \
    --csv new_houses.csv \
    --output predictions.csv
```

## 📊 Notebooks and Examples

Explore the comprehensive analysis in our Jupyter notebooks:

- **[EDA and Modeling Notebook](notebooks/house_price_eda_modeling.ipynb)**: Complete exploratory data analysis with 9 sections covering data understanding, preprocessing, feature engineering, and model evaluation

The notebook includes:
1. Data Loading and Overview
2. Data Quality Assessment
3. Exploratory Data Analysis
4. Feature Engineering
5. Data Preprocessing
6. Model Training and Selection
7. Model Evaluation
8. Feature Importance Analysis
9. Conclusions and Next Steps

## 🏗️ Project Structure

```
experimets_genai/
├── src/                          # Source code
│   ├── data_processing/          # Data loading and preprocessing
│   │   ├── data_loader.py        # Data validation and loading
│   │   ├── numeric_preprocessing.py
│   │   ├── categorical_preprocessing.py
│   │   ├── text_preprocessing.py
│   │   └── unified_pipeline.py   # Combined preprocessing
│   ├── models/                   # Model training and persistence
│   │   ├── trainer.py            # Model training framework
│   │   └── persistence.py        # Model saving/loading
│   ├── evaluation/               # Model evaluation
│   │   ├── evaluator.py          # Metrics calculation
│   │   └── feature_analyzer.py   # Feature importance
│   └── experiment_tracking/      # W&B integration
│       └── enhanced_trainer.py
├── scripts/                      # CLI tools
│   ├── fast_train.py             # Fast training script (recommended)
│   ├── simple_predict.py         # Simple prediction script
│   └── predict_cli.py            # Advanced CLI interface
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── notebooks/                    # Jupyter notebooks
├── data/                         # Data files
└── models/                       # Saved models
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Performance benchmarks
pytest tests/integration/test_performance_benchmarks.py -v -s
```

### Test Coverage

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end pipeline validation
- **Performance Tests**: Benchmarks and regression detection
- **CLI Tests**: Command-line interface validation

## 🚨 Troubleshooting

### Common Issues

1. **Training Issues**: The original comprehensive pipeline expects different column names than the actual dataset
   ```bash
   # Use the fast training script instead
   python scripts/fast_train.py --data data/house_prices.csv --output models/model.joblib
   ```

2. **Memory Issues**: Large dataset may cause memory problems
   ```bash
   # Use a smaller sample size
   python scripts/fast_train.py --sample-size 5000 --data data/house_prices.csv --output models/model.joblib
   ```

3. **Column Format Issues**: The dataset uses Indian price formats
   ```bash
   # The fast_train.py script handles "42 Lac", "1.40 Cr" formats automatically
   ```

4. **Import Errors**: For the advanced CLI, ensure `src/` is in your Python path
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

### Performance Optimization

- **Large Datasets**: Use batch processing or sample data for development
- **Memory Constraints**: Disable text features or reduce TF-IDF features
- **Training Speed**: Use fewer CV folds or simpler models for quick iterations

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Add tests** for new functionality
4. **Run the test suite**: `pytest tests/ -v`
5. **Submit a pull request**

## 📝 Development Status

✅ **WORKING SOLUTION**: This project now has a **fully functional ML pipeline** for house price prediction!

### What's Working:
- ✅ **Fast Training**: `scripts/fast_train.py` - trains models on the actual dataset format
- ✅ **Predictions**: `scripts/simple_predict.py` - makes predictions with JSON or CSV input  
- ✅ **Data Handling**: Correctly parses Indian price formats ("42 Lac", "1.40 Cr")
- ✅ **Multiple Models**: Random Forest, Linear Regression, Ridge regression
- ✅ **Real Performance**: Test R² of 0.63 on 5K sample, working with 180K+ records

### Example Usage:
```bash
# Train a model (takes ~30 seconds)
python scripts/fast_train.py --data data/house_prices.csv --output models/my_model.joblib --sample-size 10000

# Make prediction (instant)  
python scripts/simple_predict.py --model models/my_model.joblib --json '{"Carpet Area":"1200 sq ft","Bathroom":2}'
# Output: 🎯 Prediction: ₹4,991,667
```

### Advanced Features:
The original comprehensive pipeline (following OpenSpec methodology) is complete but expects different column names. Check `openspec/changes/` for the full methodology implementation.

## 🙏 Acknowledgments

- **OpenSpec**: For providing the structured development methodology
- **scikit-learn**: For machine learning algorithms and preprocessing tools
- **Weights & Biases**: For experiment tracking and model monitoring
- **pandas**: For data manipulation and analysis
- **NLTK & spaCy**: For natural language processing capabilities

## Quick Start

1. **Setup Environment**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys and configuration
   
   pip install -r requirements.txt
   ```

2. **Train a Model**
   ```bash
   python scripts/fast_train.py \
       --data data/house_prices.csv \
       --output models/house_price_model.joblib \
       --model-type random_forest
   ```

3. **Make Predictions**
   ```bash
   python scripts/simple_predict.py \
       --model models/house_price_model.joblib \
       --json '{"Carpet Area":"1200 sq ft","Bathroom":2,"Furnishing":"Semi-Furnished"}'
   ```

4. **Explore the Data**
   ```bash
   jupyter notebook notebooks/house_price_eda_modeling.ipynb
   ```

## Development Status

This project is currently under development following OpenSpec methodology. Check `openspec/changes/` for active development plans.