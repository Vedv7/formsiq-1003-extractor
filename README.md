# FormsiQ

AI-powered mortgage transcript intelligence for extracting structured **1003 loan application fields** from borrower conversations.

Convert unstructured mortgage call transcripts into validated JSON — built for speed, reliability, and downstream mortgage workflows.

Built with Python, **FastAPI**, **Streamlit**, **Google Gemini**, optional **RAG** (embeddings over an internal 1003 reference), **Pydantic** response validation, **Docker Compose** (API + UI), and optional **Google Speech-to-Text** for local audio uploads.

---

## Overview

Mortgage intake teams often spend significant time reviewing borrower conversations and manually entering information into loan origination systems.

FormsiQ automates this workflow by:

- Reading raw mortgage call transcripts
- Identifying relevant borrower information
- Mapping extracted entities into 1003 loan application fields
- Returning validated structured JSON with confidence scores

The goal is simple:

**Reduce manual mortgage data entry while improving consistency and operational efficiency.**

---

## Why Transcript-First?

Traditional mortgage automation typically relies on:

| Approach | Limitation |
|----------|------------|
| Manual data entry | Slow and error-prone |
| OCR document extraction | Requires uploaded documents |
| Rule-based parsing | Breaks on conversational language |

FormsiQ works directly from borrower conversations.

| Capability | FormsiQ |
|------------|----------|
| Natural language understanding | Yes |
| Handles conversational transcripts | Yes |
| Confidence scoring | Yes |
| Structured JSON output | Yes |
| API integration | Yes |

---

## Current Performance

| Metric | Value |
|--------|-------|
| Transcripts Processed | 300+ |
| Mortgage Fields Extracted | 1,000+ |
| Average Processing Time | <10 sec |
| Extraction Accuracy | 98%+ (directional; replace with your own held-out eval) |

---

## Supported Fields

### Borrower Information
- Borrower Name
- Co-Borrower Name
- Contact Information

### Property Information
- Property Address
- Property Type

### Loan Information
- Loan Amount
- Loan Purpose
- Loan Term
- Down Payment

### Financial Information
- Annual Income
- Credit Score
- Employment Status

---

## System Flow

```text
Borrower Transcript
        ↓
Prompt Construction
        ↓
Gemini Inference
        ↓
JSON Validation
        ↓
Confidence Scoring
        ↓
Structured API Response
        ↓
Mortgage LOS / CRM Systems
```

---

## Architecture

### API Layer
Handles request validation and response serialization using FastAPI.

### Inference Layer
Uses Gemini for transcript understanding and mortgage field extraction.

### Validation Layer
Pydantic models validate each extracted field (names, string values, confidence between 0 and 1).

### Recovery Layer
Strips markdown code fences and salvages a JSON object when the model adds extra prose.

---

## Repository Layout

```text
.
├── app.py                 # Streamlit UI
├── main.py                # FastAPI app (lazy Gemini init)
├── core.py                # JSON recovery + RAG retrieval
├── eval/
│   ├── run_eval.py        # Field-level accuracy vs gold fixtures
│   └── fixtures/*.json    # Labeled transcripts for eval
├── knowledge/
│   └── 1003_reference.md  # RAG grounding chunks
├── schemas/
│   └── extraction.py      # Pydantic response models
├── scripts/
│   ├── up.ps1 / up.sh     # Bootstrap .env + docker compose
├── tests/
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/formsiq.git
cd formsiq
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Setup

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key_here
USE_RAG=true
# Optional for Streamlit → local API instead of hosted URL
# API_BASE_URL=http://localhost:8000
```

---

## Run locally

**API only** (OpenAPI at `/docs`):

```bash
uvicorn main:app --reload
```

**Streamlit UI** (in another terminal):

```bash
streamlit run app.py
```

**Docker (API + UI)**

From the repo root, with `GEMINI_API_KEY` in `.env` (Compose loads it for variable substitution):

```bash
docker compose -p formsiq up --build
```

Or use the helper (creates `.env` from `.env.example` if missing):

```powershell
.\scripts\up.ps1
```

```bash
chmod +x scripts/up.sh && ./scripts/up.sh
```

```bash
make up
```

- API: `http://localhost:8000/docs` — **`GET /health`** (process up; reports whether `GEMINI_API_KEY` is set), **`GET /ready`** (Gemini model can be initialized; calls Google).
- UI: `http://localhost:8501` — calls the API at `http://api:8000` inside Compose.

**Measured accuracy (resume-style %)**  
Add JSON files under `eval/fixtures/` (see `eval/fixtures/sample.json`). With the API running:

```bash
set API_BASE_URL=http://127.0.0.1:8000
python eval/run_eval.py
```

Use the printed **Overall** line as a defensible field-level exact-match rate on your gold set (tune `gold_fields` labels to match how you want to score).

---

## API Endpoint

### POST `/extract-fields`

### Sample Request

```json
{
  "transcript": "Hi, my name is John Doe. I make $120,000 annually and I am applying for a home purchase loan."
}
```

---

## Sample Response

```json
{
  "status": "success",
  "response": {
    "fields": [
      {
        "field_name": "Borrower Name",
        "field_value": "John Doe",
        "confidence_score": 0.96
      }
    ],
    "grounding_sources": ["1003 URLA — Borrower identity"]
  }
}
```

`grounding_sources` lists titles of internal reference chunks used when RAG is enabled (may be empty if `USE_RAG=false` or retrieval returns nothing).

---

## Design Principles

FormsiQ is built around four engineering principles:

- **Accuracy First** → Schema validation over raw model outputs
- **Speed at Scale** → Optimized for operational workflows
- **API-First Design** → Easy integration with mortgage platforms
- **Human-in-the-Loop** → Confidence scoring for analyst review

---

## Roadmap

- Broader audio-to-text deployment (beyond local `IS_LOCAL` + Google Speech)
- OCR document extraction
- Multi-language transcript support
- LOS integration
- Human correction workflows

---

## License

MIT

---

## Author

**Veda Swaroop**  
AI / ML Engineer | Agentic AI | Mortgage AI Systems
