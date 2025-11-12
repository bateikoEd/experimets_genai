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

# Define the target normalized record
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

raw_text = """
Vendor: ACME Corp. Main contact: Ms. Alice <alice@acme.io>, phone (212)555-0199.
HQ: 1 Liberty Plaza, New York, NY 10006. Tags: enterprise, priority.
"""

if client:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role":"user",
                "content": f"""Return ONLY valid JSON with keys: name, email, phone, address({{street,city,state,zip}}), tags[].
If unavailable, use null or empty list. No extra text, no markdown fences.

TEXT:
{raw_text}
"""
            }],
            # No response_format schema here; we rely on instruction
            temperature=0
        )
        
        import json
        try:
            candidate = json.loads(resp.choices[0].message.content)  # Parse the response content
            record = NormalizedRecord(**candidate)    # still validate with Pydantic
            print("✅ Non-structured output result:")
            print(record.model_dump())
        except (json.JSONDecodeError, ValidationError) as e:
            # cost risk: you may need a repair pass (extra tokens)
            print("Needs repair:", e)
    except Exception as e:
        print(f"❌ API call failed: {e}")
        # Show mock data for demonstration
        mock_data = {
            "name": "ACME Corp",
            "email": "alice@acme.io",
            "phone": "(212)555-0199",
            "address": {
                "street": "1 Liberty Plaza",
                "city": "New York",
                "state": "NY",
                "zip": "10006"
            },
            "tags": ["enterprise", "priority"]
        }
        record = NormalizedRecord(**mock_data)
        print("📝 Mock non-structured output result:")
        print(record.model_dump())
else:
    # Demo with mock data when API key is not available
    mock_data = {
        "name": "ACME Corp",
        "email": "alice@acme.io",
        "phone": "(212)555-0199",
        "address": {
            "street": "1 Liberty Plaza",
            "city": "New York",
            "state": "NY", 
            "zip": "10006"
        },
        "tags": ["enterprise", "priority"]
    }
    record = NormalizedRecord(**mock_data)
    print("📝 Mock non-structured output result (API key not configured):")
    print(record.model_dump())
