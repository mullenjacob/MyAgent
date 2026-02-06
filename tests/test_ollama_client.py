from types import SimpleNamespace

import requests

from openclaw_local.config import ModelConfig
from openclaw_local.ollama_client import OllamaClient


def test_status_ok(monkeypatch) -> None:
    def fake_get(url, timeout):
        assert url.endswith("/api/tags")
        return SimpleNamespace(
            json=lambda: {"models": [{"name": "llama3"}]},
            raise_for_status=lambda: None,
        )

    monkeypatch.setattr(requests, "get", fake_get)
    client = OllamaClient(ModelConfig())
    status = client.status()
    assert status["ok"] is True
    assert status["models"] == ["llama3"]


def test_status_error(monkeypatch) -> None:
    def fake_get(url, timeout):
        raise requests.RequestException("boom")

    monkeypatch.setattr(requests, "get", fake_get)
    client = OllamaClient(ModelConfig())
    status = client.status()
    assert status["ok"] is False
    assert status["models"] == []
    assert "boom" in status["error"]
