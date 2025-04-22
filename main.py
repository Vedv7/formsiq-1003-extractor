import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

import vertexai
from vertexai.preview.generative_models import GenerativeModel

import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler
import logging

# --- Auth fix for Render ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/gcp-key.json"

# --- Logging ---
client = google.cloud.logging.Client()
handler = CloudLoggingHandler(client)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(handler)
logger = logging.getLogger("formsiq.extractor")

# --- Vertex Init ---
load_dotenv()
vertexai.init(project="iconic-episode-256420", location="us-central1")
MODEL = GenerativeModel("gemini-1.5-flash")

# --- FastAPI ---
app = FastAPI(
    title="Mortgage Field Extractor",
    description="Extracts 1003 loan fields using Gemini AI",
    version="1.0"
)

class TranscriptInput(BaseModel):
    transcript: str

class FieldResponse(BaseModel):
    status: str
    response: str

@app.post("/extract-fields", response_model=FieldResponse)
async def extract_fields(data: TranscriptInput):
    logger.info("🔍 Request received for field extraction")

    try:
        prompt = generate_prompt()
        response = MODEL.generate_content(prompt + "\n\n" + data.transcript)

        try:
            parsed = json.loads(response.text)
            logger.info("✅ Parsed successfully")
        except json.JSONDecodeError:
            parsed = response.text
            logger.warning("⚠️ Response is not valid JSON")

        return {
            "status": "success",
            "response": parsed
        }

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
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

