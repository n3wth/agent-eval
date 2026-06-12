"""Hermes preset: the HTTP adapter pointed at a hermes-webui instance.

Hermes (the worked example throughout the docs) is reachable two ways — the
messaging bridge and the ACP coding surface. This preset drives the HTTP
surface; point ``url`` at your hermes-webui chat endpoint. For the ACP
surface, or if your bridge speaks a different shape, override ``payload`` and
``response_field`` in configs/hermes.yaml — the preset is plain http-adapter
config, nothing Hermes-specific is load-bearing in code.

P4 (cross-surface memory) needs two adapters for the same agent: run the
memory probes once with the tell on this surface and the trigger on the
other. See probes/memory.yaml.
"""

from __future__ import annotations

from .http import HTTPAdapter

HERMES_DEFAULTS = {
    "url": "http://localhost:8080/api/chat",
    "payload": {"session_id": "{session_id}", "message": "{message}"},
    "response_field": "reply",
    "timeout": 600,
}


class HermesAdapter(HTTPAdapter):
    name = "hermes"

    def __init__(self, config: dict | None = None):
        merged = dict(HERMES_DEFAULTS)
        merged.update(config or {})
        super().__init__(merged)
