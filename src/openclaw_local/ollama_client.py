from __future__ import annotations

import json
from typing import Any, Dict, List

import requests

from openclaw_local.config import ModelConfig


class OllamaClient:
    def __init__(self, config: ModelConfig) -> None:
        self._config = config

    def chat(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "model": self._config.model,
            "messages": messages,
            "stream": False,
        }
        response = requests.post(
            f"{self._config.base_url}/api/chat",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=self._config.request_timeout_s,
        )
        response.raise_for_status()
        return response.json()
