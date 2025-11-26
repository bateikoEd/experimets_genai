from __future__ import annotations

import json
import time
from typing import Dict

import httpx

from app.config import Settings, get_settings


class LMStudioClient:
    """Thin HTTP client for LM Studio with graceful offline fallback."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.lm_studio_url
        self.api_key = self.settings.lm_studio_api_key
        self.model = self.settings.lm_studio_model
        self._offline_helper = OfflineLLM()

    def health_check(self) -> Dict[str, str | float]:
        if not self.base_url:
            return {"status": "offline", "model": self.model}
        start = time.perf_counter()
        try:
            response = httpx.get(f"{self.base_url}/v1/health", timeout=5.0)
            response.raise_for_status()
            latency = (time.perf_counter() - start) * 1000
            payload = response.json()
            return {"status": payload.get("status", "ok"), "latency_ms": latency}
        except httpx.HTTPError:
            return {"status": "degraded"}

    def generate(self, prompt: str) -> str:
        if not self.base_url:
            return self._offline_helper.generate(prompt)
        body = {
            "model": self.model,
            "prompt": prompt,
            "temperature": 0.2,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = httpx.post(
            f"{self.base_url}/v1/completions", data=json.dumps(body), headers=headers, timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        if "choices" in data:
            return data["choices"][0]["text"].strip()
        return str(data)


class OfflineLLM:
    """Deterministic fallback used in tests and offline development."""

    def generate(self, prompt: str) -> str:
        sentences = [line.strip() for line in prompt.splitlines() if line.strip()]
        explanation = sentences[-1] if sentences else "Insufficient context"
        return f"Based on available housing data, {explanation}"
