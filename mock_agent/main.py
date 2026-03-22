"""
Mock Agent Service — simulates a real AI agent.

Exposes POST /execute and handles:
  - translate_text
  - summarize_text
  - classify_text
  - echo (fallback)
"""
import time
from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock Agent", version="0.1.0")


class ExecuteRequest(BaseModel):
    task_id: str
    capability: str
    payload: Dict[str, Any] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/execute")
def execute(req: ExecuteRequest):
    start = time.time()

    capability = req.capability
    payload = req.payload

    if capability == "translate_text":
        text = payload.get("text", "")
        target = payload.get("target_language", "de")
        result = {
            "translated_text": f"[{target.upper()}] {text}",
            "source_language": payload.get("source_language", "en"),
            "target_language": target,
        }

    elif capability == "summarize_text":
        text = payload.get("text", "")
        result = {
            "summary": text[:100] + ("..." if len(text) > 100 else ""),
            "original_length": len(text),
            "summary_length": min(len(text), 100),
        }

    elif capability == "classify_text":
        text = payload.get("text", "")
        categories = payload.get("categories", ["positive", "negative", "neutral"])
        # Simple mock: pick category based on text length
        category = categories[len(text) % len(categories)] if categories else "unknown"
        result = {
            "label": category,
            "confidence": 0.91,
            "text": text,
        }

    else:
        # Echo fallback for unknown capabilities
        result = {"echo": payload, "capability": capability}

    latency_ms = round((time.time() - start) * 1000 + 50, 2)  # add simulated 50ms

    return {
        "success": True,
        "result": result,
        "metrics": {"latency_ms": latency_ms},
    }
