from __future__ import annotations

import argparse

from openclaw_local.agent import OpenClawAgent
from openclaw_local.config import AppConfig, ModelConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw Local CLI")
    parser.add_argument("--model", default="llama3", help="Ollama model name")
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama base URL",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = AppConfig(model=ModelConfig(base_url=args.base_url, model=args.model))
    agent = OpenClawAgent(config)

    print("OpenClaw Local (type 'exit' to quit)")
    while True:
        prompt = input("> ").strip()
        if prompt.lower() in {"exit", "quit"}:
            break
        if not prompt:
            continue
        response = agent.ask(prompt)
        print(response)


if __name__ == "__main__":
    main()
