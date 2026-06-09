"""OpenClaw preset: the shell adapter with OpenClaw defaults.

OpenClaw is driven through its CLI; continuity lives in workspace files
(MEMORY.md plus the memory/ directory), which is what makes the wiped-memory
cold-start pass and the NullMemory control cheap to run against it.

The defaults below match a stock install. CLI flags and workspace paths have
moved across OpenClaw releases (and its earlier names), so configs/openclaw.yaml
overrides any of them — check ``openclaw --help`` and your workspace location
before a real run. Every key here is plain shell-adapter config; nothing
OpenClaw-specific is load-bearing in code.
"""

from __future__ import annotations

from .shell import ShellAdapter

OPENCLAW_DEFAULTS = {
    "command": [
        "openclaw",
        "agent",
        "--session-id",
        "{session_id}",
        "--message",
        "{message}",
    ],
    "response": "text",
    "timeout": 600,
    "memory_paths": [
        "~/.openclaw/workspace/MEMORY.md",
        "~/.openclaw/workspace/memory",
    ],
}


class OpenClawAdapter(ShellAdapter):
    name = "openclaw"

    def __init__(self, config: dict | None = None):
        merged = dict(OPENCLAW_DEFAULTS)
        merged.update(config or {})
        super().__init__(merged)
