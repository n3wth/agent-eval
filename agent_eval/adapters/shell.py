"""Generic subprocess adapter: any agent with a CLI.

Config:

    adapter: shell
    command: ["my-agent", "chat", "--session", "{session_id}", "--message", "{message}"]
    response: text            # or "json:path.to.field"
    timeout: 300
    cwd: ~/work               # optional
    env: { MY_AGENT_FLAG: "1" }   # optional, merged over the parent env
    memory_paths: ["~/.my-agent/memory"]   # optional, enables memory control

``{session_id}`` and ``{message}`` are substituted per send. If the CLI has
no session flag, omit ``{session_id}`` — but then every send is its own
conversation and the memory probes measure the agent's persistent store
directly, which is usually what you want for a CLI agent.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from .base import Adapter, MemoryControl, Reply, Session
from .files import FileMemoryControl


def extract_json_path(data, path: str):
    cur = data
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


class ShellSession(Session):
    def __init__(self, adapter: "ShellAdapter", session_id: str | None = None):
        super().__init__(session_id)
        self.adapter = adapter

    def _send(self, message: str) -> Reply:
        cfg = self.adapter.config
        command = [
            arg.format(message=message, session_id=self.id)
            for arg in cfg["command"]
        ]
        env = dict(os.environ)
        env.update({k: str(v) for k, v in (cfg.get("env") or {}).items()})
        cwd = cfg.get("cwd")
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=cfg.get("timeout", 300),
                cwd=str(Path(cwd).expanduser()) if cwd else None,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return Reply(text="", error="timeout")
        if proc.returncode != 0:
            return Reply(
                text=proc.stdout or "",
                raw=proc.stderr,
                error=f"exit {proc.returncode}: {proc.stderr.strip()[:500]}",
            )
        out = proc.stdout.strip()
        response = cfg.get("response", "text")
        if response.startswith("json:"):
            try:
                data = json.loads(out)
                return Reply(text=str(extract_json_path(data, response[5:])), raw=data)
            except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
                return Reply(text=out, error=f"response parse failed: {e}")
        return Reply(text=out)


class ShellAdapter(Adapter):
    name = "shell"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        if "command" not in self.config:
            raise ValueError("shell adapter requires a 'command' list")
        self._memory: MemoryControl | None = None
        if self.config.get("memory_paths"):
            self._memory = FileMemoryControl(
                self.config["memory_paths"], self.config.get("memory_backup_dir")
            )

    def start_session(self, session_id: str | None = None) -> Session:
        return ShellSession(self, session_id)

    @property
    def memory_control(self) -> MemoryControl | None:
        return self._memory
