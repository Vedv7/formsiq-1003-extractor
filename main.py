import os

# Tell GCP libraries where your static JSON key is
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/gcp-key.json"









from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import vertexai
from vertexai.language_models import TextGenerationModel

import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler
import logging

# Initialize the client
client = google.cloud.logging.Client()

# Set up handler manually
handler = CloudLoggingHandler(client)

# Apply to root logger
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(handler)

# Optional named logger (you can remove if not needed)
logger = logging.getLogger("formsiq.extractor")

# --- Vertex AI Init ---
load_dotenv()
vertexai.init(project="iconic-episode-256420", location="us-central1")
MODEL = TextGenerationModel.from_pretrained("gemini-1.5-pro")

# --- FastAPI Setup ---
app = FastAPI(
    title="Mortgage Field Extractor",
    description="Extracts 1003 loan fields using Gemini AI",
    version="1.0"
)

# --- Request Model ---
class TranscriptInput(BaseModel):
    transcript: str

# --- Response Model (optional Swagger doc clarity) ---
class FieldResponse(BaseModel):
    status: str
    response: str

# --- Endpoint ---
@app.post("/extract-fields", response_model=FieldResponse)
async def extract_fields(data: TranscriptInput):
    logger.info("🔍 Received request for field extraction")

    try:
        prompt = generate_prompt()
        logger.debug("📋 Prompt generated")

        response = MODEL.predict(
            prompt + "\n\n" + data.transcript,
            temperature=0.2,
            max_output_tokens=1024
        )
        logger.info("🤖 Prediction returned from Gemini")

        try:
            parsed = json.loads(response.text)
            logger.info("✅ Parsed response successfully")
        except json.JSONDecodeError:
            parsed = response.text
            logger.warning("⚠️ Response not valid JSON. Raw response returned.")

        return {
            "status": "success",
            "response": parsed
        }

    except Exception as e:
        logger.error(f"❌ Field extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- Prompt ---
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
