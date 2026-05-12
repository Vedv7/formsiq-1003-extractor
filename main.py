from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from contextlib import asynccontextmanager
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

from core import parse_model_json, retrieve_grounding, warmup_retriever
from schemas.extraction import ExtractionResponse

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USE_RAG = os.getenv("USE_RAG", "true").lower() == "true"

_model_lock = threading.Lock()
_model: Any | None = None


def select_model() -> str:
    available_models = [m.name for m in genai.list_models()]
    logger.info("Available Gemini models: %s", available_models)
    for preferred in [
        "models/gemini-2.0-flash-latest",
        "models/gemini-1.5-flash-latest",
        "models/gemini-1.5-pro-latest",
    ]:
        if preferred in available_models:
            logger.info("Selected model: %s", preferred)
            return preferred
    raise RuntimeError("No suitable Gemini model found: " + ", ".join(available_models))


def _ensure_model_sync() -> Any:
    """Lazy-init Gemini (import no longer calls Google; Docker /health stays fast)."""
    global _model
    with _model_lock:
        if _model is not None:
            return _model
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        genai.configure(api_key=api_key)
        model_name = select_model()
        _model = genai.GenerativeModel(model_name=model_name)
        return _model


@asynccontextmanager
async def lifespan(app: FastAPI):
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        genai.configure(api_key=key)
    else:
        logger.warning("GEMINI_API_KEY missing at startup: embeddings/RAG may use keyword fallback only.")
    await asyncio.to_thread(warmup_retriever)
    yield


app = FastAPI(
    title="Mortgage Field Extractor",
    description="Extracts 1003 loan fields using Gemini, schema validation, and optional RAG grounding.",
    version="1.2",
    lifespan=lifespan,
)


class TranscriptInput(BaseModel):
    transcript: str


def generate_prompt(rag_block: str) -> str:
    rag_section = ""
    if rag_block.strip():
        rag_section = (
            "\n\n## Retrieved reference (grounding)\n\n"
            + rag_block.strip()
            + "\n\n---\n"
        )
    return f"""
You are an expert mortgage assistant trained to extract information for the 1003 Uniform Residential Loan Application form from customer service call transcripts.
{rag_section}

From the transcript provided, extract ONLY the fields listed below **if they are clearly mentioned**. For each field, return:
- field_name
- field_value
- confidence_score (between 0 and 1, reflecting clarity in the transcript)

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
{{
  "fields": [
    {{
      "field_name": "Borrower Name",
      "field_value": "John Doe",
      "confidence_score": 0.94
    }}
  ]
}}
"""


def _sync_generate(full_prompt: str) -> str:
    model = _ensure_model_sync()
    response = model.generate_content(full_prompt)
    text = getattr(response, "text", None)
    if not text:
        parts = []
        for c in getattr(response, "candidates", []) or []:
            content = getattr(c, "content", None)
            for p in getattr(content, "parts", []) or []:
                t = getattr(p, "text", None)
                if t:
                    parts.append(t)
        text = "\n".join(parts) if parts else ""
    if not text:
        raise ValueError("Empty response from Gemini")
    return text


@app.post("/extract-fields")
async def extract_fields(data: TranscriptInput, use_rag: bool = True):
    transcript = data.transcript.strip()
    if len(transcript) < 5:
        raise HTTPException(status_code=400, detail="Transcript too short")

    try:
        await asyncio.to_thread(_ensure_model_sync)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    rag_block = ""
    sources: list[str] = []
    if USE_RAG and use_rag:
        rag_block, sources = await asyncio.to_thread(retrieve_grounding, transcript, 3)

    prompt = generate_prompt(rag_block)
    full_prompt = prompt + "\n\n## Call transcript\n\n" + transcript

    try:
        raw = await asyncio.to_thread(_sync_generate, full_prompt)
        payload = parse_model_json(raw)
        if "fields" not in payload:
            raise ValueError("JSON must contain a 'fields' array")
        validated = ExtractionResponse.model_validate(
            {"fields": payload["fields"], "grounding_sources": sources}
        )
    except json.JSONDecodeError as e:
        logger.exception("JSON decode failed")
        raise HTTPException(status_code=422, detail=f"Model returned invalid JSON: {e}") from e
    except ValidationError as e:
        logger.warning("Schema validation failed: %s", e)
        raise HTTPException(
            status_code=422,
            detail={"message": "Extraction failed schema validation", "errors": e.errors()},
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Extraction error")
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"status": "success", "response": validated.model_dump()}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "gemini_api_key_set": bool(os.getenv("GEMINI_API_KEY", "").strip()),
    }


@app.get("/ready")
async def ready():
    """Readiness: API key present and Gemini model can be selected (may call Google)."""
    if not os.getenv("GEMINI_API_KEY", "").strip():
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not set")
    try:
        await asyncio.to_thread(_ensure_model_sync)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"status": "ready"}
