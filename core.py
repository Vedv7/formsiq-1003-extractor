"""Single module: JSON recovery from model output + RAG grounding (narrow surface for main.py)."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Sequence

import google.generativeai as genai

logger = logging.getLogger(__name__)

# --- JSON recovery ---------------------------------------------------------------------------

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def strip_code_fences(text: str) -> str:
    t = text.strip()
    t = _FENCE.sub("", t).strip()
    return t


def extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_model_json(raw: str) -> dict[str, Any]:
    cleaned = strip_code_fences(raw)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    blob = extract_json_object(cleaned) or extract_json_object(raw)
    if not blob:
        raise ValueError("No JSON object found in model output")
    data = json.loads(blob)
    if not isinstance(data, dict):
        raise ValueError("Model JSON root must be an object")
    return data


# --- RAG --------------------------------------------------------------------------------------

KNOWLEDGE_PATH = Path(__file__).resolve().parent / "knowledge" / "1003_reference.md"
EMBEDDING_MODEL = "models/text-embedding-004"

_titles: list[str] = []
_chunks: list[str] = []
_embeddings: list[list[float]] | None = None


def _parse_chunks(text: str) -> list[tuple[str, str]]:
    headers = list(re.finditer(r"^# [^\n]+", text, flags=re.MULTILINE))
    out: list[tuple[str, str]] = []
    for i, m in enumerate(headers):
        title_line = m.group(0)
        title = title_line.lstrip("#").strip()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[start:end].strip()
        chunk = f"{title_line}\n{body}".strip()
        out.append((title, chunk))
    return out


def _embed(text: str) -> list[float] | None:
    try:
        r = genai.embed_content(model=EMBEDDING_MODEL, content=text[:8000])
        emb = r.get("embedding")
        if isinstance(emb, list) and emb:
            return emb
    except Exception as e:
        logger.warning("Embedding call failed: %s", e)
    return None


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _keyword_scores(query: str, chunks: list[str]) -> list[float]:
    qwords = set(re.findall(r"[a-z0-9]+", query.lower()))
    if not qwords:
        return [0.0] * len(chunks)
    scores: list[float] = []
    for ch in chunks:
        cwords = set(re.findall(r"[a-z0-9]+", ch.lower()))
        scores.append(len(qwords & cwords) / max(len(qwords), 1))
    return scores


def warmup_retriever() -> None:
    global _titles, _chunks, _embeddings
    if not KNOWLEDGE_PATH.is_file():
        logger.warning("Knowledge file missing: %s", KNOWLEDGE_PATH)
        return
    raw = KNOWLEDGE_PATH.read_text(encoding="utf-8").strip()
    parsed = _parse_chunks(raw)
    if not parsed:
        logger.warning("No chunks parsed from knowledge file")
        return
    _titles = [t for t, _ in parsed]
    _chunks = [c for _, c in parsed]
    vectors: list[list[float]] = []
    for ch in _chunks:
        v = _embed(ch)
        if v is None:
            _embeddings = None
            logger.warning("Chunk embedding failed; using keyword RAG fallback only")
            return
        vectors.append(v)
    _embeddings = vectors
    logger.info("RAG index warmed: %d chunks", len(_chunks))


def retrieve_grounding(transcript: str, top_k: int = 3) -> tuple[str, list[str]]:
    if not _chunks:
        return "", []

    query = transcript.strip()
    if not query:
        return "", []

    scores: list[tuple[float, int]] = []

    if _embeddings is not None:
        qv = _embed(query[:8000])
        if qv is not None:
            for i, ev in enumerate(_embeddings):
                scores.append((_cosine(qv, ev), i))

    if not scores:
        kw = _keyword_scores(query, _chunks)
        scores = [(kw[i], i) for i in range(len(_chunks))]

    scores.sort(reverse=True)
    picked = scores[: min(top_k, len(scores))]
    idxs = sorted({i for _, i in picked})

    blocks: list[str] = []
    titles_out: list[str] = []
    for i in idxs:
        titles_out.append(_titles[i])
        blocks.append(_chunks[i])

    if not blocks:
        return "", []

    header = (
        "The following internal 1003 / URLA reference excerpts were retrieved for grounding. "
        "Use them only to interpret terminology and field meaning; extract values strictly from the call transcript.\n"
    )
    return header + "\n\n---\n\n".join(blocks), titles_out
