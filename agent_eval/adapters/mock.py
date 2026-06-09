"""Mock adapter: a toy agent with a toy memory, for tests and dry runs.

It lets the whole pipeline run offline, and its behaviors are the named
failure modes from the docs, so the tests can assert the harness catches
them:

- ``good`` — stores standing instructions ("never X", "always Y"), drops
  ephemeral ones ("just for this task").
- ``hoarder`` — stores everything, including the ephemeral. High durability
  plus high over-application; the pair must catch it.
- ``amnesiac`` — stores nothing. The no-warming agent.

Replies echo the prompt; remembered instructions are appended in an
``[applying: ...]`` block so checks can read what the toy memory did.
``rules`` (regex -> reply, optionally cycling) make flaky behavior scriptable
for the pass^k tests.
"""

from __future__ import annotations

import re

from .base import Adapter, MemoryControl, Reply, Session

STANDING = re.compile(r"\b(never|always|from now on)\b", re.I)
EPHEMERAL = re.compile(r"\b(just for|just this once|only this once|for this one task)\b", re.I)


class MockMemoryControl(MemoryControl):
    def __init__(self, adapter: "MockAdapter"):
        self.adapter = adapter
        self._stash: dict[str, list[str]] = {}

    def wipe(self) -> str:
        token = f"t{len(self._stash)}"
        self._stash[token] = list(self.adapter.memory)
        self.adapter.memory.clear()
        return token

    def restore(self, token: str) -> None:
        self.adapter.memory = list(self._stash[token])


class MockSession(Session):
    def __init__(self, adapter: "MockAdapter", session_id: str | None = None):
        super().__init__(session_id)
        self.adapter = adapter

    def _send(self, message: str) -> Reply:
        a = self.adapter
        behavior = a.config.get("behavior", "good")
        if behavior != "amnesiac":
            is_standing = bool(STANDING.search(message))
            is_ephemeral = bool(EPHEMERAL.search(message))
            if is_standing and not is_ephemeral:
                a.memory.append(message)
            elif is_ephemeral and behavior == "hoarder":
                a.memory.append(message)

        text = None
        for rule in a.config.get("rules", []):
            if re.search(rule["match"], message, re.I):
                replies = rule.get("replies") or [rule["reply"]]
                idx = a._rule_counts.setdefault(rule["match"], 0)
                a._rule_counts[rule["match"]] += 1
                text = replies[idx % len(replies)]
                break
        if text is None:
            text = f"ok: {message[:80]}"
        if a.memory:
            text += "\n[applying: " + " | ".join(a.memory) + "]"
        return Reply(text=text)


class MockAdapter(Adapter):
    name = "mock"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.memory: list[str] = []
        self._rule_counts: dict[str, int] = {}
        self._memory_control = MockMemoryControl(self)

    def start_session(self, session_id: str | None = None) -> Session:
        return MockSession(self, session_id)

    @property
    def memory_control(self) -> MemoryControl | None:
        return self._memory_control
