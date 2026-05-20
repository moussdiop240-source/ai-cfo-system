"""
LLM Adapter — unified interface for Anthropic and Ollama.

Priority:
  1. Explicit backend= argument
  2. LLM_BACKEND env var  ("anthropic" | "ollama")
  3. Auto-detect: Anthropic if ANTHROPIC_API_KEY is set, else Ollama

No API key changes needed — just switch LLM_BACKEND or pass backend="ollama".
"""
import json
import os
from typing import Any, Dict, List, Optional

import httpx

# ── defaults ────────────────────────────────────────────────────────────────
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_OLLAMA_MODEL    = "llama3.2"
DEFAULT_OLLAMA_HOST     = "http://localhost:11434"


class LLMAdapter:
    """
    Drop-in replacement for direct Anthropic or Ollama calls.
    Use complete() for raw text, complete_json() for structured output.
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        model:   Optional[str] = None,
        ollama_host: Optional[str] = None,
    ):
        self.ollama_host = (
            ollama_host
            or os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
        ).rstrip("/")

        requested = backend or os.getenv("LLM_BACKEND", "auto")

        if requested == "auto":
            self.backend = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "ollama"
        elif requested in ("anthropic", "ollama"):
            self.backend = requested
        else:
            raise ValueError(f"Unknown backend '{requested}'. Use 'anthropic' or 'ollama'.")

        if model:
            self._model = model
        elif self.backend == "anthropic":
            self._model = os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
        else:
            self._model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)

    # ── public properties ────────────────────────────────────────────────────

    @property
    def active_backend(self) -> str:
        return self.backend

    @property
    def active_model(self) -> str:
        return self._model

    # ── core interface ───────────────────────────────────────────────────────

    def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 2000,
    ) -> str:
        """Return raw text completion from whichever backend is active."""
        if self.backend == "anthropic":
            return self._anthropic_complete(system, user, max_tokens)
        return self._ollama_complete(system, user, max_tokens, json_mode=False)

    def complete_json(
        self,
        system: str,
        user: str,
        keys: List[str],
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        Request a JSON object from the model.
        `keys` is the list of top-level keys expected in the response dict.
        Falls back to best-effort extraction on parse failure.
        """
        json_instruction = (
            "\n\nRESPOND WITH A VALID JSON OBJECT ONLY — no markdown, no prose."
            f"\nRequired keys: {json.dumps(keys)}"
        )
        augmented_system = system + json_instruction

        if self.backend == "anthropic":
            text = self._anthropic_complete(augmented_system, user, max_tokens)
        else:
            text = self._ollama_complete(augmented_system, user, max_tokens, json_mode=True)

        return _extract_json(text)

    # ── Anthropic ────────────────────────────────────────────────────────────

    def _anthropic_complete(self, system: str, user: str, max_tokens: int) -> str:
        import anthropic  # lazy import — not needed for Ollama path
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text

    # ── Ollama ───────────────────────────────────────────────────────────────

    def _ollama_complete(
        self, system: str, user: str, max_tokens: int, json_mode: bool
    ) -> str:
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.1},
        }
        if json_mode:
            payload["format"] = "json"

        try:
            resp = httpx.post(
                f"{self.ollama_host}/api/chat",
                json=payload,
                timeout=httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=10.0),
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.ollama_host}. "
                "Make sure Ollama is running: `ollama serve`"
            )

    # ── utility ──────────────────────────────────────────────────────────────

    def list_ollama_models(self) -> List[str]:
        """Returns names of locally available Ollama models."""
        try:
            resp = httpx.get(f"{self.ollama_host}/api/tags", timeout=5.0)
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []

    def check_ollama_health(self) -> bool:
        try:
            resp = httpx.get(self.ollama_host, timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def status_line(self) -> str:
        if self.backend == "anthropic":
            key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
            return f"Anthropic | {self._model} | key={'SET' if key_set else 'MISSING'}"
        healthy = self.check_ollama_health()
        return f"Ollama | {self._model} | {self.ollama_host} | {'running' if healthy else 'offline'}"


# ── JSON extraction helper ───────────────────────────────────────────────────

def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    # strip markdown fences
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.lstrip("json").strip()
            if part.startswith("{"):
                text = part
                break
    # direct JSON
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    # find first { ... }
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract JSON from LLM response:\n{text[:400]}")


# ── prompt trimmer for slow local models ─────────────────────────────────────

def trim_for_local(text: str, max_chars: int = 3000) -> str:
    """Truncate a long prompt to fit local model context limits."""
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n[...trimmed for local model...]\n\n" + text[-half:]


# ── module-level singleton ────────────────────────────────────────────────────

_singleton: Optional[LLMAdapter] = None


def get_adapter(
    backend: Optional[str] = None,
    model:   Optional[str] = None,
    ollama_host: Optional[str] = None,
) -> LLMAdapter:
    """Return a shared adapter instance (or a new one if params are given)."""
    global _singleton
    if backend or model or ollama_host:
        return LLMAdapter(backend=backend, model=model, ollama_host=ollama_host)
    if _singleton is None:
        _singleton = LLMAdapter()
    return _singleton


def reset_adapter() -> None:
    """Force re-creation of the singleton (useful when env vars change)."""
    global _singleton
    _singleton = None
