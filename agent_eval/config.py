"""Eval config: which agent, which judge, where runs land.

    agent:
      adapter: openclaw            # shell | http | openclaw | hermes | mock
      # ...adapter options (see agent_eval/adapters/)
    judge:                         # optional LLM judge for `llm` checks
      adapter: shell
      command: ["claude", "-p", "{message}"]
    runs_dir: runs
    name: openclaw-mini            # label on scorecards
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .adapters import Adapter, build_adapter


class EvalConfig:
    def __init__(self, data: dict, path: str | None = None):
        if "agent" not in data:
            raise ValueError(f"{path or 'config'}: missing 'agent' section")
        self.data = data
        self.runs_dir = data.get("runs_dir", "runs")
        self.name = data.get("name", data["agent"].get("adapter", "agent"))

    @classmethod
    def load(cls, path: str | Path) -> "EvalConfig":
        return cls(yaml.safe_load(Path(path).read_text()), str(path))

    def build_agent(self) -> Adapter:
        return build_adapter(self.data["agent"])

    def build_judge(self) -> Adapter | None:
        judge = self.data.get("judge")
        return build_adapter(judge) if judge else None
