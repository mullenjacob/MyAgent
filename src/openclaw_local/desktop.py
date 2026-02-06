from __future__ import annotations

import argparse
import importlib
import threading
import time
from wsgiref.simple_server import WSGIServer

from werkzeug.serving import make_server

from openclaw_local.config import AppConfig, ModelConfig
from openclaw_local.ui import create_app


class ServerThread(threading.Thread):
    def __init__(self, host: str, port: int, app) -> None:
        super().__init__(daemon=True)
        self._server: WSGIServer = make_server(host, port, app)

    def run(self) -> None:
        self._server.serve_forever()

    def shutdown(self) -> None:
        self._server.shutdown()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw Local Desktop App")
    parser.add_argument("--model", default="llama3", help="Ollama model name")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8080, help="Bind port")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if importlib.util.find_spec("webview") is None:
        raise RuntimeError("pywebview is required for desktop app mode. Install requirements.txt")

    webview = importlib.import_module("webview")

    config = AppConfig(model=ModelConfig(base_url=args.base_url, model=args.model))
    app = create_app(config)

    server = ServerThread(args.host, args.port, app)
    server.start()
    time.sleep(0.5)

    url = f"http://{args.host}:{args.port}"
    try:
        webview.create_window("OpenClaw Local", url, width=1280, height=800)
        webview.start()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
