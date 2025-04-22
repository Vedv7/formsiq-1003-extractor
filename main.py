import os
import json
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

import vertexai
from vertexai.preview.generative_models import GenerativeModel

# --- Auth for Render ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/gcp-key.json"

# --- Logging ---
client = google.cloud.logging.Client()
handler = CloudLoggingHandler(client)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(handler)
logger = logging.getLogger("formsiq.extractor")

# --- Vertex AI Init ---
load_dotenv()
vertexai.init(project="iconic-episode-256420", location="us-central1")
model = GenerativeModel("gemini-1.5-flash")  # Use flash or 1.5-pro only if access enabled

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
    logger.info("📥 Received transcript for extraction")

    try:
        prompt = generate_prompt()
        response = model.generate_content(prompt + "\n\n" + data.transcript)

        try:
            parsed = json.loads(response.text)
            logger.info("✅ JSON parsed successfully")
        except json.JSONDecodeError:
            parsed = response.text
            logger.warning("⚠️ Response is not valid JSON")

        return {
            "status": "success",
            "response": parsed
        }

    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}", exc_info=True)
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


