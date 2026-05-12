from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator


class ExtractedField(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=256)
    field_value: str = Field(..., max_length=8192)
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    @field_validator("field_name", mode="after")
    @classmethod
    def strip_field_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("field_value", mode="before")
    @classmethod
    def stringify_value(cls, v):
        if v is None:
            return ""
        if isinstance(v, (int, float)):
            return str(v)
        return str(v)


class ExtractionResponse(BaseModel):
    fields: List[ExtractedField] = Field(default_factory=list)
    grounding_sources: List[str] = Field(
        default_factory=list,
        description="Titles/snippets of internal 1003 reference chunks used for RAG grounding.",
    )
