# pip install dspy-ai openai pydantic python-dotenv
import dspy, json
from typing import Optional, List
from pydantic import BaseModel, Field, ValidationError
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

# 1) Wire DSPy to your OpenAI model
try:
    if openai_api_key:
        print("✅ OpenAI API key loaded from .env file")
        # Try different DSPy OpenAI model configurations
        try:
            lm = dspy.LM(model="openai/gpt-4o-mini", temperature=0, api_key=openai_api_key)
        except:
            lm = dspy.OpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key)
    else:
        print("✅ OpenAI API key loaded from environment")
        # Try different DSPy OpenAI model configurations
        try:
            lm = dspy.LM(model="openai/gpt-4o-mini", temperature=0)
        except:
            lm = dspy.OpenAI(model="gpt-4o-mini", temperature=0)
    
    dspy.settings.configure(lm=lm)
    api_available = True
    print("✅ DSPy configured with OpenAI API")
except Exception as e:
    print(f"❌ OpenAI API not available: {e}")
    print("📝 Running in demo mode with mock data")
    api_available = False

# 2) Define the task signature
class NormalizeSig(dspy.Signature):
    """Normalize contact text into a compact JSON object."""
    text = dspy.InputField(desc="raw contact text")
    json_out = dspy.OutputField(desc="ONLY compact JSON, no prose")

# 3) Define a program (one-step)
class Normalizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.step = dspy.Predict(NormalizeSig)

    def forward(self, text: str):
        # keep instruction focused (optimizer will refine this)
        prompt = (
            "Extract name, email, phone, address {street,city,state,zip}, tags[]. "
            "Return ONLY valid minified JSON with those keys."
        )
        out = self.step(text=prompt + "\n\nTEXT:\n" + text)
        return out

program = Normalizer()

# 4) A few labeled examples (tiny train/dev) - Convert to DSPy Examples
trainset = [
    dspy.Example(text="Jane Roe <jroe@ex.io> 22 Pine Ave, Boston, MA 02110", 
                 json_out='{"name":"Jane Roe","email":"jroe@ex.io","phone":null,"address":{"street":"22 Pine Ave","city":"Boston","state":"MA","zip":"02110"},"tags":[]}').with_inputs("text"),
    dspy.Example(text="Vendor ACME UK; contact bob@acme.co.uk, +44 20 7946 0101; 221B Baker St, London", 
                 json_out='{"name":"ACME UK","email":"bob@acme.co.uk","phone":"+44 20 7946 0101","address":{"street":"221B Baker St","city":"London","state":null,"zip":null},"tags":["vendor"]}').with_inputs("text"),
]
devset = [
    dspy.Example(text="J. Smith, 10 Main St, Denver CO 80202, phone 303-555-0123; js@smith.io",
                 json_out='{"name":"J. Smith","email":"js@smith.io","phone":"303-555-0123","address":{"street":"10 Main St","city":"Denver","state":"CO","zip":"80202"},"tags":[]}').with_inputs("text")
]

# 5) Define a simple metric (exact JSON keys + Pydantic validation)
def metric(example, pred, trace=None):
    try:
        obj = json.loads(pred.json_out)
        NormalizedRecord(**obj)  # must validate
        return 1.0
    except Exception:
        return 0.0

# 6) Optimize the prompt/few-shots automatically
if api_available:
    try:
        print("\n🔍 Original prompt structure:")
        # Show original prompt before optimization
        original_pred = program(text=devset[0]["text"])
        print("Original prediction:", original_pred.json_out)
        
        print("\n⚙️ Running DSPy optimization...")
        optim = dspy.BootstrapFewShot(metric=metric, max_bootstrapped_demos=4, max_rounds=2)
        optimized_program = optim.compile(student=program, trainset=trainset)
        
        # 7) Evaluate on dev example
        pred = optimized_program(text=devset[0]["text"])
        print("\n✅ DSPy optimized result:")
        print("Pred JSON:", pred.json_out)  # should already be compact + on-schema
        
        # Display the optimized prompt
        print("\n📝 Optimized Prompt Inspection:")
        try:
            # Try to access the optimized prompt structure
            if hasattr(optimized_program, 'step') and hasattr(optimized_program.step, 'signature'):
                print("Signature:", optimized_program.step.signature)
            
            # Show the demos/examples that were bootstrapped
            if hasattr(optimized_program, 'step') and hasattr(optimized_program.step, 'demos'):
                print(f"Number of bootstrapped demos: {len(optimized_program.step.demos)}")
                for i, demo in enumerate(optimized_program.step.demos):
                    print(f"Demo {i+1}: {demo}")
            
            # If available, show the actual prompt template
            if hasattr(optimized_program.step, 'extended_signature'):
                print("Extended signature:", optimized_program.step.extended_signature)
                
        except Exception as prompt_error:
            print(f"Could not extract full prompt details: {prompt_error}")
            print("Optimized program type:", type(optimized_program))
            print("Available attributes:", [attr for attr in dir(optimized_program) if not attr.startswith('_')])
            
    except Exception as e:
        print(f"❌ DSPy optimization failed: {e}")
        print("📝 Showing mock result:")
        mock_result = '{"name":"J. Smith","email":"js@smith.io","phone":"303-555-0123","address":{"street":"10 Main St","city":"Denver","state":"CO","zip":"80202"},"tags":[]}'
        print("Mock JSON:", mock_result)
else:
    print("📝 Mock DSPy result (API not available):")
    mock_result = '{"name":"J. Smith","email":"js@smith.io","phone":"303-555-0123","address":{"street":"10 Main St","city":"Denver","state":"CO","zip":"80202"},"tags":[]}'
    print("Mock JSON:", mock_result)
