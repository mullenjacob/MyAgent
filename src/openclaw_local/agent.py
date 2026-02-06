from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import requests

from openclaw_local.config import AppConfig
from openclaw_local.ollama_client import OllamaClient
from openclaw_local.tools import ToolExecutor

SYSTEM_PROMPT = """
You are OpenClaw Local, a local-first assistant running on the user's Windows PC.
You can answer questions and solve problems. When needed, you can call tools.

Tool call format:
If you need to call a tool, respond with ONLY valid JSON like:
{"tool": "tool_name", "args": {"arg": "value"}}

Available tools and arguments:
- list_dir: {"path": "optional path"}
- read_file: {"path": "file path"}
- write_file: {"path": "file path", "content": "text"}
- run_command: {"command": "shell command"}
- camera_snapshot: {}
- open_google_tab: {"query": "search query"}
- send_whatsapp_message: {"phone": "international number", "message": "message"}
- open_file: {"path": "file path"}
- open_url: {"url": "https://..."}

If no tool is required, respond normally.
""".strip()


class OpenClawAgent:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = OllamaClient(config.model)
        self._tools = ToolExecutor(config.tool)
        self._messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def _try_parse_tool_call(self, content: str) -> Dict[str, Any] | None:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        if "tool" not in payload:
            return None
        if "args" not in payload or not isinstance(payload["args"], dict):
            payload["args"] = {}
        return payload

    def _append_tool_result(self, tool: str, result: str) -> None:
        self._messages.append(
            {"role": "assistant", "content": json.dumps({"tool": tool, "result": result})}
        )


    def _direct_tool_intent(self, text: str) -> str | None:
        normalized = text.strip()

        m = re.match(r"(?:open|search) google(?: for)? (.+)$", normalized, re.I)
        if m:
            result = self._tools.open_google_tab(m.group(1))
            return result.output

        m = re.match(r"send (?:a )?whatsapp message to (\+?\d+) saying (.+)$", normalized, re.I)
        if m:
            result = self._tools.send_whatsapp_message(phone=m.group(1), message=m.group(2))
            return result.output

        m = re.match(r"open file (.+)$", normalized, re.I)
        if m:
            result = self._tools.open_file_with_default_app(m.group(1).strip())
            return result.output

        m = re.match(r"open url (https?://\S+)$", normalized, re.I)
        if m:
            result = self._tools.open_url(m.group(1))
            return result.output

        return None

    def ask(self, text: str) -> str:
        direct = self._direct_tool_intent(text)
        if direct is not None:
            return direct

        self._messages.append({"role": "user", "content": text})
        try:
            response = self._client.chat(self._messages)
        except requests.RequestException as exc:
            return (
                "I'm unable to reach the local model right now. "
                "Please try again after confirming Ollama is running."
            )
        content = response["message"]["content"]
        tool_call = self._try_parse_tool_call(content)
        if tool_call:
            tool_name = tool_call["tool"]
            result = self._tools.execute(tool_name, tool_call.get("args", {}))
            self._append_tool_result(tool_name, result.output)
            try:
                follow_up = self._client.chat(self._messages)
            except requests.RequestException:
                return result.output
            return follow_up["message"]["content"]
        self._messages.append({"role": "assistant", "content": content})
        return content

    def status(self) -> Dict[str, Any]:
        return self._client.status()
