# Project Dependencies

This file documents the project dependencies declared in `requirements.txt` and provides a Mermaid diagram grouping runtime and development/test dependencies.

## Runtime / Core dependencies
- pandas >= 2.0.0
- numpy >= 1.24.0
- scikit-learn >= 1.3.0
- scipy >= 1.10.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- plotly >= 5.15.0
- nltk >= 3.8
- spacy >= 3.6.0
- textblob >= 0.17.0
- wandb >= 0.15.0
- joblib >= 1.3.0
- jupyter >= 1.0.0
- ipykernel >= 6.20.0
- notebook >= 6.5.0
- databricks-connect >= 13.0.0
- pyspark >= 3.4.0
- great-expectations >= 0.17.0
- python-dotenv >= 1.0.0
- click >= 8.1.0
- pyyaml >= 6.0
- tqdm >= 4.65.0

## Development / Testing / Formatting tools
- pytest >= 7.4.0
- pytest-cov >= 4.1.0
- black >= 23.0.0
- flake8 >= 6.0.0
- isort >= 5.12.0

## Optional (commented in `requirements.txt`)
- xgboost >= 1.7.0 (optional)
- lightgbm >= 4.0.0 (optional)
- catboost >= 1.2.0 (optional)

---

## Mermaid dependency diagram
Paste the block below into a Mermaid renderer (GitHub, VS Code Mermaid preview, Mermaid Live Editor) to visualize the grouping and high-level associations.

```mermaid
flowchart TD
  subgraph Runtime["Runtime / Core"]
    direction TB
    pandas["pandas\n>=2.0.0"]
    numpy["numpy\n>=1.24.0"]
    sklearn["scikit-learn\n>=1.3.0"]
    scipy["scipy\n>=1.10.0"]
    matplotlib["matplotlib\n>=3.7.0"]
    seaborn["seaborn\n>=0.12.0"]
    plotly["plotly\n>=5.15.0"]
    nltk["nltk\n>=3.8"]
    spacy["spacy\n>=3.6.0"]
    textblob["textblob\n>=0.17.0"]
    wandb["wandb\n>=0.15.0"]
    joblib["joblib\n>=1.3.0"]
    jupyter["jupyter\n>=1.0.0"]
    ipykernel["ipykernel\n>=6.20.0"]
    notebook["notebook\n>=6.5.0"]
    databricks["databricks-connect\n>=13.0.0"]
    pyspark["pyspark\n>=3.4.0"]
    ge["great-expectations\n>=0.17.0"]
    dotenv["python-dotenv\n>=1.0.0"]
    click["click\n>=8.1.0"]
    pyyaml["pyyaml\n>=6.0"]
    tqdm["tqdm\n>=4.65.0"]
  end

  subgraph Dev["Development / Testing"]
    direction TB
    pytest["pytest\n>=7.4.0"]
    pytestcov["pytest-cov\n>=4.1.0"]
    black["black\n>=23.0.0"]
    flake8["flake8\n>=6.0.0"]
    isort["isort\n>=5.12.0"]
  end

  subgraph Optional["Optional (commented)"]
    direction TB
    xgb["xgboost (optional)\n>=1.7.0"]
    lgbm["lightgbm (optional)\n>=4.0.0"]
    cat["catboost (optional)\n>=1.2.0"]
  end

  %% Typical associations
  pandas --> numpy
  sklearn --> numpy
  sklearn --> scipy
  seaborn --> matplotlib
  plotly --> pandas
  spacy --> nltk
  textblob --> nltk
  joblib --> sklearn
  wandb --> joblib
  databricks --> pyspark
  ge --> pandas
  pytest --> pytestcov
  black --> isort
```

---

If you'd like this diagram exported to PNG/SVG, I can render it locally if you allow running a renderer or provide a preferred output format.
