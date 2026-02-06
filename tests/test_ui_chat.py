import openclaw_local.ui as ui
from openclaw_local.config import AppConfig, ModelConfig


class FakeAgent:
    def __init__(self, config):
        self.model = config.model.model

    def ask(self, text: str) -> str:
        return f"[{self.model}] {text}"

    def status(self):
        return {"ok": True, "models": ["llama3", "mistral"], "error": None}


def test_chat_lifecycle(monkeypatch) -> None:
    monkeypatch.setattr(ui, "OpenClawAgent", FakeAgent)
    app = ui.create_app(AppConfig(model=ModelConfig(model="llama3")))
    client = app.test_client()

    chats_resp = client.get("/api/chats")
    chats = chats_resp.get_json()["chats"]
    assert len(chats) == 1
    chat_id = chats[0]["id"]

    msg_resp = client.post(f"/api/chats/{chat_id}/messages", json={"message": "hello"})
    assert msg_resp.get_json()["reply"] == "[llama3] hello"

    switch_resp = client.post(f"/api/chats/{chat_id}/model", json={"model": "mistral"})
    assert switch_resp.get_json()["ok"] is True

    msg_resp_2 = client.post(f"/api/chats/{chat_id}/messages", json={"message": "again"})
    assert msg_resp_2.get_json()["reply"] == "[mistral] again"
