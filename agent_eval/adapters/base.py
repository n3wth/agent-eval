"""Adapter contract: the seam that keeps the harness agent-neutral.

An adapter wraps one running agent (OpenClaw, Hermes, anything with a CLI or
an HTTP endpoint) behind three capabilities:

1. Sessions — ``start_session()`` returns a fresh conversation. Cross-session
   continuity is the thing the memory probes measure, so "fresh session" must
   mean what it means for that agent (new conversation id, not a cleared
   prompt).
2. Send — ``Session.send(message)`` returns the agent's reply as text.
3. Memory control (optional) — wipe/restore for the cold-start pass and
   enable/disable for the NullMemory control. Adapters that can't control
   memory still run the suite; the memory probes record the missing control
   instead of silently skipping it.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Reply:
    text: str
    raw: Any = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class Session(ABC):
    def __init__(self, session_id: str | None = None):
        self.id = session_id or uuid.uuid4().hex[:12]
        self.transcript: list[dict[str, str]] = []

    @abstractmethod
    def _send(self, message: str) -> Reply: ...

    def send(self, message: str) -> Reply:
        reply = self._send(message)
        self.transcript.append({"role": "user", "text": message})
        self.transcript.append({"role": "agent", "text": reply.text})
        return reply

    def close(self) -> None:
        pass


class MemoryUnsupported(RuntimeError):
    pass


class MemoryControl(ABC):
    """Wipe/restore (tenure passes) and enable/disable (NullMemory control).

    Per docs/tenure.md: move aside, never delete. ``wipe`` must be reversible
    by ``restore``.

    ``checkpoint``/``rollback`` are the copy-based pair behind probe
    isolation: a checkpoint survives any number of rollbacks, so every probe
    can start from the same baseline state. Optional — adapters that can't
    copy their store simply don't support ``--isolate``.
    """

    @abstractmethod
    def wipe(self) -> str:
        """Set memory aside; return a token that ``restore`` accepts."""

    @abstractmethod
    def restore(self, token: str) -> None: ...

    def checkpoint(self) -> str:
        """Snapshot memory without disturbing it. Reusable across rollbacks."""
        raise MemoryUnsupported(f"{type(self).__name__} cannot checkpoint")

    def rollback(self, token: str) -> None:
        """Return memory to a checkpoint, keeping the checkpoint valid."""
        raise MemoryUnsupported(f"{type(self).__name__} cannot rollback")

    @property
    def supports_isolation(self) -> bool:
        return type(self).checkpoint is not MemoryControl.checkpoint

    def set_enabled(self, enabled: bool) -> None:
        """Toggle memory for the NullMemory control. Default: wipe/restore."""
        if not enabled:
            self._null_token = self.wipe()
        else:
            token = getattr(self, "_null_token", None)
            if token is not None:
                self.restore(token)
                self._null_token = None


class Adapter(ABC):
    name = "base"

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    def start_session(self, session_id: str | None = None) -> Session: ...

    @property
    def memory_control(self) -> MemoryControl | None:
        return None

    def close(self) -> None:
        pass


@dataclass
class AdapterSpec:
    """What a config file names: the adapter and its options."""

    adapter: str
    options: dict = field(default_factory=dict)
