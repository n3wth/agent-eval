"""Runnable harness for the coworker eval.

The method lives in the markdown docs (docs/proposal.md and friends); this
package is its executable half. The invariants the docs guard are enforced
here in code:

- D1 is reported as pass^k (all-of-k succeed), never pass@1 alone.
- D2 is a pair: durability is not reportable without discrimination.
- D5 is the RAIR/RSR 2x2, never delegation volume.
- Memory probes refuse to run if the trigger restates the planted fact.
- Every memory probe carries a NullMemory control where the adapter allows it.
"""

__version__ = "0.1.0"
