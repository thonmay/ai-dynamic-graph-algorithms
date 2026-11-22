# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Agent layer: who writes and repairs candidates.

The orchestrator talks to one ``Backend`` (see ``base.py``) with three
operations, generate / repair / reflect. Backends:

  api       built-in tool loop over any OpenAI-compatible chat endpoint
            (OpenRouter, OpenAI, local servers); the model only returns
            tool calls, this package executes them (``tools.py``)
  opencode  an agent harness driven headlessly; the harness owns the tools
  mock      scripted, for tests and demos
"""

from .base import Backend, CallResult, make_backend

__all__ = ["Backend", "CallResult", "make_backend"]
