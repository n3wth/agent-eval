"""Adapter registry. ``adapter: <name>`` in a config file resolves here.

openclaw and hermes are presets over the generic shell and http adapters:
the agent-specific knowledge is default config, not code, so a CLI flag
rename costs a YAML edit, not a patch.
"""

from __future__ import annotations

from .base import Adapter, AdapterSpec, MemoryControl, MemoryUnsupported, Reply, Session
from .hermes import HermesAdapter
from .http import HTTPAdapter
from .mock import MockAdapter
from .openclaw import OpenClawAdapter
from .shell import ShellAdapter

REGISTRY: dict[str, type[Adapter]] = {
    "shell": ShellAdapter,
    "http": HTTPAdapter,
    "openclaw": OpenClawAdapter,
    "hermes": HermesAdapter,
    "mock": MockAdapter,
}


def build_adapter(config: dict) -> Adapter:
    """Build an adapter from a config dict with an ``adapter`` key."""
    config = dict(config)
    name = config.pop("adapter", None)
    if name not in REGISTRY:
        known = ", ".join(sorted(REGISTRY))
        raise ValueError(f"unknown adapter {name!r}; known: {known}")
    return REGISTRY[name](config)


__all__ = [
    "Adapter",
    "AdapterSpec",
    "MemoryControl",
    "MemoryUnsupported",
    "Reply",
    "Session",
    "REGISTRY",
    "build_adapter",
]
