"""Generic HTTP adapter: any agent with a JSON endpoint.

Config:

    adapter: http
    url: http://localhost:8080/api/chat
    payload: { session_id: "{session_id}", message: "{message}" }
    response_field: reply          # dot path into the JSON response
    headers: { Authorization: "Bearer ${HERMES_TOKEN}" }
    timeout: 300
    memory_paths: ["~/.my-agent/memory"]   # optional

``${VAR}`` in headers expands from the environment, so tokens stay out of
config files. Stdlib urllib only; no client dependency.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import Adapter, MemoryControl, Reply, Session
from .files import FileMemoryControl
from .shell import extract_json_path


def _fill(template, message: str, session_id: str):
    if isinstance(template, str):
        return template.format(message=message, session_id=session_id)
    if isinstance(template, dict):
        return {k: _fill(v, message, session_id) for k, v in template.items()}
    if isinstance(template, list):
        return [_fill(v, message, session_id) for v in template]
    return template


class HTTPSession(Session):
    def __init__(self, adapter: "HTTPAdapter", session_id: str | None = None):
        super().__init__(session_id)
        self.adapter = adapter

    def _send(self, message: str) -> Reply:
        cfg = self.adapter.config
        payload = _fill(
            cfg.get("payload", {"session_id": "{session_id}", "message": "{message}"}),
            message,
            self.id,
        )
        headers = {"Content-Type": "application/json"}
        for k, v in (cfg.get("headers") or {}).items():
            headers[k] = os.path.expandvars(str(v))
        req = urllib.request.Request(
            cfg["url"],
            data=json.dumps(payload).encode(),
            headers=headers,
            method=cfg.get("method", "POST"),
        )
        try:
            with urllib.request.urlopen(req, timeout=cfg.get("timeout", 300)) as resp:
                body = resp.read().decode()
        except urllib.error.URLError as e:
            return Reply(text="", error=f"http error: {e}")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return Reply(text=body)
        field = cfg.get("response_field")
        if field:
            try:
                return Reply(text=str(extract_json_path(data, field)), raw=data)
            except (KeyError, IndexError, ValueError) as e:
                return Reply(text=body, raw=data, error=f"response parse failed: {e}")
        return Reply(text=body, raw=data)


class HTTPAdapter(Adapter):
    name = "http"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        if "url" not in self.config:
            raise ValueError("http adapter requires a 'url'")
        self._memory: MemoryControl | None = None
        if self.config.get("memory_paths"):
            self._memory = FileMemoryControl(
                self.config["memory_paths"], self.config.get("memory_backup_dir")
            )

    def start_session(self, session_id: str | None = None) -> Session:
        return HTTPSession(self, session_id)

    @property
    def memory_control(self) -> MemoryControl | None:
        return self._memory
