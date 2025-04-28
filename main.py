from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import google.generativeai as genai

# Load API Key from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="Mortgage Field Extractor", description="Extracts 1003 loan fields using Gemini AI", version="1.0")

# Choose one of the available models
def select_model():
    available_models = [m.name for m in genai.list_models()]
    print("✅ Available Models:", available_models)

    # Prefer flash if you saw it working in console
    for preferred in [
        "models/gemini-1.5-flash-latest",
        "models/gemini-2.0-flash-latest",
        "models/gemini-1.5-pro-latest"
    ]:
        if preferred in available_models:
            print(f"✅ Selected Model: {preferred}")
            return preferred

    raise RuntimeError("❌ No suitable Gemini model found. Available: " + ", ".join(available_models))

# Load model
MODEL_NAME = select_model()
MODEL = genai.GenerativeModel(model_name=MODEL_NAME)

# Request body
class TranscriptInput(BaseModel):
    transcript: str

# Response body for Swagger
class FieldResponse(BaseModel):
    status: str
    response: str

@app.post("/extract-fields")
async def extract_fields(data: TranscriptInput):
    try:
        prompt = generate_prompt()
        response = MODEL.generate_content(prompt + "\n\n" + data.transcript)

        try:
            parsed = json.loads(response.text)
        except json.JSONDecodeError:
            parsed = response.text  # fallback to raw string if not clean JSON

        return {
            "status": "success",
            "response": parsed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_prompt():
    return """
You are an expert mortgage assistant trained to extract information for the 1003 Uniform Residential Loan Application form from customer service call transcripts.

From the transcript provided, extract ONLY the fields listed below **if they are clearly mentioned**. For each field, return:
- field_name
- field_value
- confidence_score (between 0 and 1)

Fields:
1. Borrower Name
2. Co-Borrower Name
3. Property Address
4. Loan Amount
5. Loan Purpose
6. Property Type
7. Employment Status
8. Annual Income
9. Credit Score
10. Loan Term
11. Down Payment
12. Contact Info

Respond strictly in raw JSON. Do NOT include any explanation or markdown. No ```json or ``` tags:
{
  "fields": [
    {
      "field_name": "Borrower Name",
      "field_value": "John Doe",
      "confidence_score": 0.94
    }
  ]
}
"""
