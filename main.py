from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import asyncio
import google.generativeai as genai

# --- Load API Key from .env ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- Hardcode Model Selection ---
MODEL_NAME = "models/gemini-2.0-flash"
MODEL = genai.GenerativeModel(model_name=MODEL_NAME)

print(f"✅ Selected Gemini Model: {MODEL_NAME}")

# --- FastAPI App ---
app = FastAPI(
    title="Mortgage Field Extractor",
    description="Extracts 1003 loan fields using Gemini 2.0 Flash",
    version="1.0"
)

# --- Request and Response Models ---
class TranscriptInput(BaseModel):
    transcript: str
from typing import Union
class FieldResponse(BaseModel):
    status: str
    response: Union[str, dict]


# --- /extract-fields Endpoint (Text Input) ---
@app.post("/extract-fields", response_model=FieldResponse)
async def extract_fields(data: TranscriptInput):
    try:
        prompt = generate_prompt()
        response = MODEL.generate_content(prompt + "\n\n" + data.transcript)

        try:
            parsed = json.loads(response.text)
        except json.JSONDecodeError:
            parsed = response.text  # fallback if not clean JSON

        return {
            "status": "success",
            "response": parsed
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- /extract-audio-fields Endpoint (Audio Upload) ---
@app.post("/extract-audio-fields", response_model=FieldResponse)
async def extract_audio_fields(audio_file: UploadFile = File(...), prompt: str = Form(...)):
    try:
        # Step 1: Save uploaded audio temporarily
        temp_audio_path = f"temp_{audio_file.filename}"
        with open(temp_audio_path, "wb") as f:
            file_content = await audio_file.read()
            f.write(file_content)

        print(f"🎵 Saved temp audio file: {temp_audio_path}, Size: {os.path.getsize(temp_audio_path)} bytes")

        await asyncio.sleep(0.5)  # tiny wait to ensure file system saves

        # Step 2: Upload audio file to Gemini
        uploaded_file = genai.upload_file(temp_audio_path)

        # Step 3: Send prompt + uploaded audio to Gemini
        response = MODEL.generate_content(
            contents=[
                prompt,
                uploaded_file
            ],
            generation_config={
                "temperature": 0.3,
                "top_p": 0.95
            }
        )

        # Step 4: Clean up
        os.remove(temp_audio_path)

        try:
            parsed = json.loads(response.text)
        except json.JSONDecodeError:
            parsed = {"transcript": response.text}

        return {
            "status": "success",
            "response": parsed
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Audio extraction failed: {str(e)}")

# --- Prompt for both text and audio extraction ---
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

