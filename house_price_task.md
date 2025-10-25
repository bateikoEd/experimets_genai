# 🧠 Task: House Price Prediction EDA & Modeling Pipeline

## 🎯 Objective
Perform a **comprehensive exploratory data analysis (EDA)** and build a **full machine learning pipeline** to predict property prices (houses and flats).  
The goal is to construct a robust, reproducible, and explainable modeling workflow integrating NLP, tabular processing, and experiment tracking.

---

## 📋 Task Definition

### 1. Exploratory Data Analysis (EDA)
- Analyze dataset structure, data types, missing values, and feature distributions.  
- Visualize numeric and categorical features, correlation with target.  
- Investigate feature interactions and potential outliers.

### 2. Feature Engineering
- **Numeric features:** impute missing values, scale using StandardScaler.  
- **Categorical features:** impute, encode via OneHotEncoder (handle rare categories).  
- **Text features:** extract from columns such as `description`, `location`, `property_title`.  
  - Use **NLTK** for tokenization, stopword removal, and n-gram generation.
  - Use **spaCy** for Named Entity Recognition (NER) counts (e.g., GPE, ORG, LOC).  
- Combine all features into unified sparse matrix via `ColumnTransformer`.  
- (Optional) Integrate **PySpark** for scalable preprocessing and loading.

### 3. Model Training & Experiment Tracking
Train and compare the following regression models:
- Linear Regression
- Ridge Regression
- Lasso Regression
- Random Forest Regressor
- Extra Trees Regressor
- Gradient Boosting Regressor (optional)

Each experiment should:
- Log parameters, metrics, and artifacts to **Weights & Biases (W&B)**.
- Compute and visualize **RMSE, MAE, and R²** for validation data.
- Select the best model based on RMSE.

### 4. Feature Importance & Explainability
- Visualize top 30 feature importances (tree-based models) or coefficients (linear models).  
- Report most influential features for price prediction.

### 5. Pipeline Persistence
- Build a **unified pipeline object** integrating:
  - Preprocessing (imputation, encoding, scaling)
  - Text vectorization (TF-IDF)
  - Trained model  
- Save using `joblib` → `artifacts/house_price_full_pipeline.joblib`.

### 6. CLI Inference Script
Provide a command-line interface script (`predict_cli.py`) to load the saved model and predict prices from either JSON or CSV input.

Example usage:
```bash
python predict_cli.py --model artifacts/house_price_full_pipeline.joblib   --json '{"carpet_area":1200,"bathroom":2,"balcony":1,"furnishing":"Semi-Furnished","property_status":"Ready to Move","description":"2BHK near park","location":"Downtown"}'
```

Output:
```json
[
  {"prediction": 7854320.12}
]
```

### 7. Deliverables
- **Jupyter Notebook:** `house_price_eda_modeling.ipynb`
- **CLI Script:** `predict_cli.py`
- **Trained Pipeline:** `house_price_full_pipeline.joblib`

---

## 🧩 Dataset Description
The **House Price dataset** provides detailed attributes for residential properties:  
- Carpet area, super area, plot area, dimensions  
- Property status, floor, furnishing, transaction type  
- Bathroom, balcony, parking, ownership type  
- Facing, overlooking, society name, property title  
- Total amount (target variable), price per square foot  
- Descriptive text fields (location, title, etc.)  

---

## 📊 Metrics & Evaluation
Use regression metrics:
- **RMSE (Root Mean Squared Error)**
- **MAE (Mean Absolute Error)**
- **R² (Coefficient of Determination)**

---

## 🧠 Notes
- Configure `WANDB_API_KEY` for experiment tracking.
- Set `TARGET_COL` environment variable if target differs from default `total_amount`.
- Adapt paths and features as per your dataset schema.

---

## 🚀 Expected Outcome
A production-ready ML pipeline capable of:
- Automatic preprocessing (numerical, categorical, and textual)
- Model training, evaluation, and experiment tracking
- Exported artifact for deployment and real-time inference
- CLI for quick, structured predictions

---

*This specification ensures a fully modular, reproducible, and enterprise-grade workflow aligning with ML engineering best practices.*
