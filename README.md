# OpenAI Examples

This folder contains examples demonstrating different approaches to using OpenAI's API for text normalization and structured output.

## Setup

### Prerequisites

1. **Python Virtual Environment**: Activate the Python 3.11 virtual environment:
   ```bash
   source ../.venv-311/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install openai pydantic python-dotenv dspy-ai
   ```

3. **API Key Configuration**: Create a `.env` file in the project root directory with your OpenAI API key:
   ```bash
   echo "OPENAI_API_KEY=your-actual-api-key-here" > ../.env
   ```

   Each example automatically loads the API key from the `.env` file using `python-dotenv` and `pydantic`.

## Examples

### 1. `strucutured-output.py`
Demonstrates **Structured Outputs** using JSON Schema to guarantee valid JSON responses.
- ✅ **Pros**: Guaranteed valid JSON, automatic validation
- ❌ **Cons**: More complex setup, requires schema definition

### 2. `not-structured-output.py` 
Shows **Non-Structured Output** relying on prompt instructions for JSON format.
- ✅ **Pros**: Simple setup, flexible
- ❌ **Cons**: May require repair passes, no guarantee of valid JSON

### 3. `prompt-optimization-dspy.py`
Uses **DSPy** for automatic prompt optimization and few-shot learning.
- ✅ **Pros**: Automatic optimization, better performance over time
- ❌ **Cons**: More complex, requires training examples

### 4. `batch_processin.py`
Demonstrates **Batch Processing** for cost-effective processing of large datasets.
- ✅ **Pros**: 50% cost reduction, efficient for large volumes
- ❌ **Cons**: Asynchronous processing, 24-hour completion window

## Running the Examples

Each example can be run independently:

```bash
# Activate virtual environment
source ../.venv-311/bin/activate

# Run individual examples
python strucutured-output.py
python not-structured-output.py  
python prompt-optimization-dspy.py
python batch_processin.py
```

## Key Features

- **Environment Variable Loading**: All examples use `python-dotenv` to load the OpenAI API key from the `.env` file
- **Graceful Fallback**: If API key is not available, examples show mock results for demonstration
- **Error Handling**: Comprehensive error handling for API failures and validation issues  
- **Pydantic Validation**: All examples use Pydantic models for data validation and serialization

## Data Model

All examples use a consistent `NormalizedRecord` schema:

```python
class Address(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None

class NormalizedRecord(BaseModel):
    name: str = Field(..., description="Full name of the customer/vendor")
    email: Optional[str] = Field(None, description="Email if found")
    phone: Optional[str] = None
    address: Address = Address()
    tags: List[str] = Field(default_factory=list)
```