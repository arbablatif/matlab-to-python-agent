"""Provider-agnostic LLM client with a disk cache and a mock mode.

Provider is chosen with LLM_PROVIDER in .env (gemini | anthropic | openai).
Every real response is cached under cache/llm/<sha256>.json, so re-running
the same conversion never pays for the same prompt twice.

Mock mode returns pre-written responses from mock_responses/<sample>/attempt_<n>.py
so the whole pipeline (conversion -> test -> retry) runs with zero API calls.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# Cheapest sensible default per provider (override with LLM_MODEL).
DEFAULT_MODELS = {
    "gemini": "gemini-3.5-flash-lite",
    "anthropic": "claude-haiku-5-5",
    "openai": "gpt-5-mini",
}


@dataclass
class LLMResponse:
    text: str
    cached: bool  # True if served from disk cache (or mock): no API cost


class LLMClient:
    def __init__(self, provider: str | None = None, model: str | None = None,
                 mock: bool = False, cache_dir: Path | None = None):
        self.mock = mock
        self.provider = "mock" if mock else (provider or os.getenv("LLM_PROVIDER") or "gemini").lower()
        if not mock and self.provider not in DEFAULT_MODELS:
            raise ValueError(f"Unknown provider '{self.provider}'. Use gemini, anthropic or openai.")
        self.model = "mock" if mock else (model or os.getenv("LLM_MODEL") or DEFAULT_MODELS[self.provider])
        self.cache_dir = cache_dir or ROOT / "cache" / "llm"
        self.api_calls = 0  # real (paid) calls made by this client

    # ------------------------------------------------------------------ public
    def complete(self, system: str, prompt: str, mock_key: tuple[str, int] | None = None) -> LLMResponse:
        """Return the model's reply. mock_key=(sample_name, attempt) is used in mock mode."""
        if self.mock:
            return LLMResponse(self._mock_reply(mock_key), cached=True)

        key = hashlib.sha256(json.dumps([self.provider, self.model, system, prompt]).encode()).hexdigest()
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            return LLMResponse(json.loads(path.read_text(encoding="utf-8"))["text"], cached=True)

        text = self._call_api(system, prompt)
        self.api_calls += 1
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"provider": self.provider, "model": self.model, "text": text},
                                   indent=2), encoding="utf-8")
        return LLMResponse(text, cached=False)

    # ----------------------------------------------------------------- private
    def _call_api(self, system: str, prompt: str) -> str:
        if self.provider == "gemini":
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            resp = client.models.generate_content(
                model=self.model, contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system, temperature=0.0))
            return resp.text or ""
        if self.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            resp = client.messages.create(model=self.model, max_tokens=8000, system=system,
                                          messages=[{"role": "user", "content": prompt}])
            return "".join(b.text for b in resp.content if b.type == "text")
        if self.provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}])
            return resp.choices[0].message.content or ""
        raise ValueError(self.provider)

    @staticmethod
    def _mock_reply(mock_key: tuple[str, int] | None) -> str:
        """Pre-written reply for (sample, attempt); falls back to the last attempt file."""
        if mock_key:
            name, attempt = mock_key
            folder = ROOT / "mock_responses" / name
            files = sorted(folder.glob("attempt_*.py")) if folder.exists() else []
            if files:
                chosen = folder / f"attempt_{attempt}.py"
                code = (chosen if chosen.exists() else files[-1]).read_text(encoding="utf-8")
                return f"```python\n{code}\n```"
        return ("```python\n# Mock mode: no canned conversion exists for this file.\n"
                "# Run without --mock to convert it with a real LLM.\n```")
