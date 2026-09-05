"""Free local AI via Ollama. Falls back to deterministic text if Ollama is down.

Never invents facts outside the provided evidence block.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:3b")
TIMEOUT_S = float(os.environ.get("OLLAMA_TIMEOUT", "90"))


def available() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def complete(
    *,
    system: str,
    user: str,
    temperature: float = 0.1,
) -> dict[str, Any]:
    """Return {ok, text, provider, model}."""
    if not available():
        return {
            "ok": False,
            "text": "",
            "provider": "fallback",
            "model": None,
            "error": "ollama_unavailable",
        }

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": temperature},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode())
        text = (data.get("message") or {}).get("content") or ""
        return {
            "ok": bool(text.strip()),
            "text": text.strip(),
            "provider": "ollama",
            "model": OLLAMA_MODEL,
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return {
            "ok": False,
            "text": "",
            "provider": "fallback",
            "model": OLLAMA_MODEL,
            "error": str(e),
        }


def grounded_complete(*, task: str, evidence: str, question: str = "") -> dict[str, Any]:
    system = (
        "You are a senior software engineer assistant. "
        "Use ONLY the EVIDENCE block. If evidence is insufficient, say so clearly. "
        "Do not invent files, APIs, tests, or causes not present in evidence. "
        "Be concise and technical."
    )
    user = f"TASK:\n{task}\n\nEVIDENCE:\n{evidence}\n"
    if question:
        user += f"\nQUESTION:\n{question}\n"
    return complete(system=system, user=user)
