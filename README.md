# FormsiQ

AI-powered mortgage transcript intelligence for extracting structured **1003 loan application fields** from borrower conversations.

Convert unstructured mortgage call transcripts into validated JSON — built for speed, reliability, and downstream mortgage workflows.

Built with Python, FastAPI, and Google Gemini.

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
| Extraction Accuracy | 98%+ |

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
Parses model outputs and enforces strict JSON formatting.

### Recovery Layer
Handles malformed model responses with structured fallback parsing.

---

## Repository Layout

```bash
formsiq/
├── app.py
├── prompts/
├── schemas/
├── utils/
├── tests/
├── assets/
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
```

---

## Run Locally

Start the FastAPI server:

```bash
uvicorn app:app --reload
```

Swagger API docs:

```text
http://localhost:8000/docs
```

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
    ]
  }
}
```

---

## Design Principles

FormsiQ is built around four engineering principles:

- **Accuracy First** → Schema validation over raw model outputs
- **Speed at Scale** → Optimized for operational workflows
- **API-First Design** → Easy integration with mortgage platforms
- **Human-in-the-Loop** → Confidence scoring for analyst review

---

## Roadmap

- Audio-to-text integration
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
