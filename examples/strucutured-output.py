# pip install openai pydantic python-dotenv
from typing import Optional, List
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI
from dotenv import load_dotenv
import os
import sys

# Add parent directory to sys.path to access .env file
sys.path.append('..')

# Try to load environment variables from .env file
env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_file_path)

# Get API key from environment
openai_api_key = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
try:
    if openai_api_key:
        client = OpenAI(api_key=openai_api_key)
        print("✅ OpenAI API key loaded from .env file")
    else:
        client = OpenAI()  # Will try to get from environment
        print("✅ OpenAI API key loaded from environment")
except Exception as e:
    print(f"❌ OpenAI API key not found. Please check your .env file or environment variables.")
    print("For demonstration purposes, we'll show the structure with mock data.")
    client = None

# 1) Define your target normalized record
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

# 2) Build a JSON Schema from Pydantic (for Structured Outputs)
json_schema = {
    "name": "NormalizedRecord",
    "schema": NormalizedRecord.model_json_schema()
}

# 3) Call the Chat Completions API with structured outputs
raw_text = """
Contact: J. Doe, e-mail john.doe(at)example.com, phone +1 415 555 0100.
Lives at 10 Market St, San Francisco, CA 94103. Interested in 'ml', 'genai'.
"""

if client:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Extract and normalize the following text into the provided schema.\n\nTEXT:\n{raw_text}"
            }],
            response_format={
                "type": "json_schema",
                "json_schema": json_schema
            },
            temperature=0
        )
        
        # 4) Parse and validate into Pydantic
        import json
        data = json.loads(resp.choices[0].message.content)  # Parse JSON from response
        record = NormalizedRecord(**data)
        print("✅ Structured output result:")
        print(record.model_dump())
    except Exception as e:
        print(f"❌ API call failed: {e}")
        # Show mock data for demonstration
        mock_data = {
            "name": "J. Doe",
            "email": "john.doe@example.com",
            "phone": "+1 415 555 0100",
            "address": {
                "street": "10 Market St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94103"
            },
            "tags": ["ml", "genai"]
        }
        record = NormalizedRecord(**mock_data)
        print("📝 Mock structured output result:")
        print(record.model_dump())
else:
    # Demo with mock data when API key is not available
    mock_data = {
        "name": "J. Doe",
        "email": "john.doe@example.com", 
        "phone": "+1 415 555 0100",
        "address": {
            "street": "10 Market St",
            "city": "San Francisco", 
            "state": "CA",
            "zip": "94103"
        },
        "tags": ["ml", "genai"]
    }
    record = NormalizedRecord(**mock_data)
    print("📝 Mock structured output result (API key not configured):")
    print(record.model_dump())
