# pip install openai pydantic python-dotenv
import json, uuid, time, pathlib
from typing import Optional, List
from pydantic import BaseModel, Field
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
        api_available = True
    else:
        client = OpenAI()  # Will try to get from environment
        print("✅ OpenAI API key loaded from environment")
        api_available = True
except Exception as e:
    print(f"❌ OpenAI API key not found: {e}")
    print("📝 Running in demo mode to show batch processing structure")
    client = None
    api_available = False

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

# 1) Build JSONL of per-item requests for the Responses API
items = [
    {"id":"1", "text":"John Smith <john@x.io> 500 Elm St, Austin, TX 78701"},
    {"id":"2", "text":"ACME GmbH, contact eva@acme.de, Alexanderplatz 1, Berlin"},
]

schema = {
    "name": "NormalizedRecord",
    "schema": NormalizedRecord.model_json_schema()
}

lines = []
for it in items:
    req = {
        "custom_id": it["id"],              # helps correlate results
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [{
                "role": "user",
                "content": f"Normalize to schema below.\n\nTEXT:\n{it['text']}"
            }],
            "response_format": {
                "type": "json_schema",
                "json_schema": schema
            },
            "temperature": 0
        }
    }
    lines.append(json.dumps(req))

batch_file = pathlib.Path("normalization_batch.jsonl")
batch_file.write_text("\n".join(lines), encoding="utf-8")
print(f"📄 Created batch file: {batch_file} with {len(lines)} requests")

if api_available:
    try:
        # 2) Upload + create batch
        uploaded = client.files.create(file=open(batch_file, "rb"), purpose="batch")
        batch = client.batches.create(
            input_file_id=uploaded.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        print("✅ Batch created:", batch.id)

        # 3) Poll (in practice: backoff / webhook)
        print("⏳ Polling for batch completion (this may take time)...")
        while True:
            b = client.batches.retrieve(batch.id)
            if b.status in ("completed", "failed", "cancelled"):
                print("🏁 Batch status:", b.status)
                break
            time.sleep(10)

        # 4) Download results
        if b.output_file_id:
            out = client.files.content(b.output_file_id).text
            results = [json.loads(line) for line in out.splitlines()]
            # Each line mirrors your custom_id and response body
            normalized = {}
            for r in results:
                cid = r["custom_id"]
                payload = r["response"]["body"]
                # Parse JSON from the chat completion response
                data = json.loads(payload["choices"][0]["message"]["content"])
                normalized[cid] = NormalizedRecord(**data).model_dump()
            print("✅ Batch processing results:")
            print(normalized)
        else:
            print("❌ No output file available")
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        print("📝 Showing mock batch results:")
        mock_results = {
            "1": {
                "name": "John Smith",
                "email": "john@x.io",
                "phone": None,
                "address": {"street": "500 Elm St", "city": "Austin", "state": "TX", "zip": "78701"},
                "tags": []
            },
            "2": {
                "name": "ACME GmbH",
                "email": "eva@acme.de",
                "phone": None,
                "address": {"street": "Alexanderplatz 1", "city": "Berlin", "state": None, "zip": None},
                "tags": []
            }
        }
        print(mock_results)
else:
    print("📝 Mock batch processing results (API not available):")
    mock_results = {
        "1": {
            "name": "John Smith",
            "email": "john@x.io", 
            "phone": None,
            "address": {"street": "500 Elm St", "city": "Austin", "state": "TX", "zip": "78701"},
            "tags": []
        },
        "2": {
            "name": "ACME GmbH",
            "email": "eva@acme.de",
            "phone": None, 
            "address": {"street": "Alexanderplatz 1", "city": "Berlin", "state": None, "zip": None},
            "tags": []
        }
    }
    print(mock_results)
