from openclaw_local.agent import OpenClawAgent
from openclaw_local.config import AppConfig


def test_direct_google_intent(monkeypatch) -> None:
    agent = OpenClawAgent(AppConfig())

    monkeypatch.setattr(
        agent._tools,
        "open_google_tab",
        lambda query: type("R", (), {"output": f"Opened Google tab: {query}"})(),
    )

    response = agent.ask("open google for local llm news")
    assert "Opened Google tab" in response


def test_direct_whatsapp_intent(monkeypatch) -> None:
    agent = OpenClawAgent(AppConfig())

    monkeypatch.setattr(
        agent._tools,
        "send_whatsapp_message",
        lambda phone, message: type("R", (), {"output": f"Opened WhatsApp compose URL for {phone}"})(),
    )

    response = agent.ask("send whatsapp message to +15551234567 saying hello")
    assert "+15551234567" in response
