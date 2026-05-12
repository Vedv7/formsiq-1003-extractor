# FormsiQ

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Vedv7/formsiq-1003-extractor/actions/workflows/ci.yml/badge.svg)](https://github.com/Vedv7/formsiq-1003-extractor/actions/workflows/ci.yml)

**Production-oriented reference implementation** for turning **mortgage call transcripts** (and optional **PDF text** or **local audio**) into **structured 1003 / URLA-style loan fields** as **schema-validated JSON** with **per-field confidence scores**, suitable for human review and downstream LOS or CRM integration.

**Stack:** Streamlit (UI) · FastAPI (API) · Google Gemini (inference) · optional **RAG grounding** (internal 1003 reference) · Pydantic (validation) · Docker Compose · optional Google Speech-to-Text (local).

> **Short GitHub description (copy for “About”):**  
> *Gemini-powered 1003 URLA field extraction from transcripts and documents — FastAPI + Streamlit, schema-validated JSON, optional RAG, Docker-ready.*

---

## Table of contents

1. [Executive summary](#executive-summary)  
2. [System context](#system-context)  
3. [Architecture](#architecture)  
4. [End-to-end workflows](#end-to-end-workflows)  
5. [Deployment topology](#deployment-topology)  
6. [API reference](#api-reference)  
7. [Configuration](#configuration)  
8. [Security & operations](#security--operations)  
9. [Quality & evaluation](#quality--evaluation)  
10. [Repository layout](#repository-layout)  
11. [Local development](#local-development)  
12. [Roadmap](#roadmap)  
13. [License](#license)  

---

## Executive summary

Mortgage intake teams routinely transcribe or read borrower conversations and manually key data into loan origination systems. FormsiQ **automates structured extraction** from natural-language transcripts by combining **LLM inference** with **strict response validation**, **robust JSON recovery** when the model wraps output in markdown, and **optional retrieval grounding** from an internal URLA-oriented knowledge base to improve field semantics.

| Design goal | How it is addressed |
|-------------|---------------------|
| Reliability | Pydantic schemas, JSON salvage pipeline, HTTP 422 on invalid payloads |
| Operability | `/health` (liveness), `/ready` (Gemini selectable), Docker Compose, CI |
| Extensibility | Pluggable `API_BASE_URL`, optional RAG via `USE_RAG`, eval harness |
| Auditability | `grounding_sources` in API responses when RAG is used |

---

## System context

High-level actors and boundaries:

```mermaid
flowchart LR
    subgraph Clients
        A[Analyst / LO]
        B[Automation / LOS]
    end
    subgraph FormsiQ
        UI[Streamlit UI]
        API[FastAPI API]
        CORE[core.py — RAG + JSON recovery]
        LLM[Google Gemini]
    end
    subgraph Optional
        STT[Google Speech-to-Text]
    end
    A --> UI
    UI -->|HTTPS JSON| API
    B -->|HTTPS JSON| API
    API --> CORE
    API --> LLM
    UI -.->|IS_LOCAL + GCP| STT
```

---

## Architecture

Logical layers (single-tenant reference deployment):

```mermaid
flowchart TB
    subgraph Presentation
        S[Streamlit app.py]
    end
    subgraph Application
        F[FastAPI main.py]
    end
    subgraph Domain
        C[core.py — retrieval + parse recovery]
        K[knowledge/1003_reference.md]
        M[schemas/extraction.py]
    end
    subgraph External
        G[Google Gemini API]
        E[Google Embeddings API]
    end
    S -->|HTTP| F
    F --> C
    C --> K
    C --> E
    F --> G
    F --> M
```

**Responsibilities**

| Layer | Responsibility |
|-------|----------------|
| **Presentation** | Input capture (paste, `.txt`, `.pdf` text, optional audio when configured), results display, export JSON. |
| **Application** | REST contract, async request handling, lazy Gemini client init, orchestration. |
| **Domain** | RAG chunk retrieval (embedding + keyword fallback), model-output JSON extraction, Pydantic validation. |
| **External** | Gemini generation; embedding API for RAG when `GEMINI_API_KEY` is available at warmup. |

---

## End-to-end workflows

### A. Synchronous extraction (API)

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant RAG as core.retrieve_grounding
    participant GEM as Gemini
    participant VAL as Pydantic

    Client->>API: POST /extract-fields {transcript}
    API->>API: Ensure model (lazy init)
    alt USE_RAG=true
        API->>RAG: retrieve_grounding(transcript)
        RAG-->>API: rag_block, grounding_sources
    end
    API->>GEM: generate_content(prompt + transcript)
    GEM-->>API: raw text
    API->>API: parse_model_json (fences / salvage)
    API->>VAL: ExtractionResponse.validate
    VAL-->>API: fields[]
    API-->>Client: 200 {status, response}
```

### B. UI-driven flow (operator)

```mermaid
flowchart TD
    Start([Operator opens UI]) --> Input{Input mode}
    Input -->|Paste / file| T[Transcript text]
    Input -->|PDF| P[pypdf text extract]
    Input -->|Audio IS_LOCAL| A[Google STT]
    P --> T
    A --> T
    T --> POST[POST to API_BASE_URL /extract-fields]
    POST --> OK{HTTP 200?}
    OK -->|yes| Show[Render field cards + confidence]
    OK -->|no| Err[Show error / retry]
```

### C. Container startup (Docker Compose)

```mermaid
flowchart LR
    subgraph compose [docker compose]
        API[api :8000]
        UI[ui :8501]
    end
    API -->|healthy| UI
    UI -->|API_BASE_URL=http://api:8000| API
```

The `ui` service waits until `api` passes its **HTTP health check** (`GET /health`) so the browser does not hit a cold API during container bring-up.

---

## Deployment topology

```mermaid
flowchart TB
    subgraph Host
        DC[docker compose -p formsiq]
    end
    subgraph Network formsiq_default
        API[api container\nuvicorn main:app]
        UI[ui container\nstreamlit app.py]
    end
    DC --> API
    DC --> UI
    Internet((Internet)) --> API
    Browser((User browser)) --> UI
    API --> Internet
```

**Ports**

| Service | Host port | Purpose |
|---------|-----------|---------|
| `api` | 8000 | REST API, OpenAPI `/docs` |
| `ui` | 8501 | Streamlit operator UI |

---

## API reference

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness; JSON includes `gemini_api_key_set` (boolean). |
| `GET` | `/ready` | Readiness: API key present and Gemini model list succeeds (calls Google). |
| `POST` | `/extract-fields` | Body: `{"transcript": "..."}`. Query: `use_rag` (default `true`). |

**Example request**

```json
{
  "transcript": "Hi, my name is John Doe. I make $120,000 annually and I am applying for a home purchase loan."
}
```

**Example response (truncated)**

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

`confidence_score` is **model-reported** (prompted) and **bounded** by Pydantic to \[0, 1\]. `grounding_sources` lists titles of internal chunks used when RAG retrieval runs; it may be empty if RAG is disabled or retrieval yields none.

---

## Configuration

| Variable | Scope | Description |
|----------|--------|-------------|
| `GEMINI_API_KEY` | API (required for extraction) | Google AI Studio / Gemini API key. |
| `USE_RAG` | API | `true` / `false` — enable retrieval grounding (default `true`). |
| `API_BASE_URL` | Streamlit | Base URL for `POST /extract-fields` (Compose sets `http://api:8000`). |
| `IS_LOCAL` | Streamlit | When `true`, enables optional Google Speech audio upload path + local GCP creds. |

Copy `.env.example` to `.env` for local and Docker Compose interpolation. **Never commit real `.env` files.**

---

## Security & operations

- **Secrets:** Store `GEMINI_API_KEY` in environment or a secret manager; rotate if ever leaked. The repository intentionally **does not** track `.env`.
- **Data handling:** This reference app does **not** implement a database; transcripts are processed in memory for the request. For production, add explicit **data retention**, **encryption in transit** (TLS termination), and **access control** in front of the API.
- **Speech / PDF:** Optional paths increase surface area — restrict `IS_LOCAL` and GCP credentials to trusted environments only.
- **Health monitoring:** Use `/health` for orchestrator liveness; use `/ready` only if you accept an outbound call to Google on each check (model init is cached in-process after first success).

---

## Quality & evaluation

- **CI:** GitHub Actions workflow (`.github/workflows/ci.yml`) runs `compileall` and `tests/test_core.py` without network or API keys.
- **Field-level eval:** Add labeled fixtures under `eval/fixtures/` and run:

```bash
export API_BASE_URL=http://127.0.0.1:8000   # Linux / macOS
# set API_BASE_URL=http://127.0.0.1:8000     # Windows CMD
python eval/run_eval.py
```

Reported **Overall** percentage is **exact match** on normalized `(field_name, value)` pairs against your gold file — use it for defensible accuracy claims after you define a sufficiently large and representative fixture set.

---

## Repository layout

```text
.
├── app.py                      # Streamlit UI
├── main.py                     # FastAPI application (lazy Gemini init)
├── core.py                     # JSON recovery + RAG retrieval
├── knowledge/
│   └── 1003_reference.md       # Internal grounding corpus (chunked)
├── schemas/
│   └── extraction.py         # Pydantic models
├── eval/
│   ├── run_eval.py
│   └── fixtures/*.json
├── scripts/
│   ├── up.ps1
│   └── up.sh
├── tests/
│   └── test_core.py
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── LICENSE
├── requirements.txt
└── README.md
```

---

## Local development

**Clone**

```bash
git clone https://github.com/Vedv7/formsiq-1003-extractor.git
cd formsiq-1003-extractor
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

**Run API + UI (two terminals)**

```bash
cp .env.example .env   # then set GEMINI_API_KEY
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

```bash
export API_BASE_URL=http://127.0.0.1:8000
streamlit run app.py
```

**Docker (recommended parity with production-like deploy)**

```bash
docker compose -p formsiq up --build
```

Helpers: `.\scripts\up.ps1`, `./scripts/up.sh`, or `make up`.

---

## Roadmap

| Priority | Item |
|----------|------|
| P1 | Hardened authn/z on API (API keys or OAuth2 proxy) |
| P1 | Structured logging + request IDs |
| P2 | Broader managed deployment for speech-to-text |
| P2 | OCR / image pipeline for scanned documents |
| P3 | Multi-language transcripts |
| P3 | LOS-specific export adapters |

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE).

---

## Author

**Veda Swaroop**  
AI / ML Engineer · Agentic systems · Mortgage automation
