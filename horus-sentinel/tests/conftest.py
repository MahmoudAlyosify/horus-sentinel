"""Test configuration.

Point the relational store at a throwaway SQLite file *before* any application module
imports the engine, so tests never touch a developer's real database.

Also isolate the suite from a developer's real ``.env``: the brain tests mock only the
self-hosted (Ollama) endpoint and assert the offline-synthesis path, so a live ``HF_TOKEN``
in ``.env`` would otherwise steer the hybrid brain to the (unmocked) Hugging Face router and
fail every reasoning test. Force the Ollama-only backend with no online credentials here.
Environment variables take precedence over ``.env`` in pydantic-settings, and these are set
before ``core.config`` is first imported, so they win regardless of ``.env`` contents.
"""

import os
import tempfile

# Must run before `core.db` (and anything importing it) is first imported.
_TMP_DB = os.path.join(tempfile.gettempdir(), "horus_sentinel_test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TMP_DB}")

# Hermetic brain: self-hosted transport only, no online credentials. Must run before
# `core.config` is first imported so these override any value in the developer's `.env`.
# Hard-set (not setdefault) so an exported HF_TOKEN in the shell can't re-break the suite.
os.environ["BRAIN_BACKEND"] = "ollama"
os.environ["HF_TOKEN"] = ""
os.environ["HF_ENDPOINT_URL"] = ""

# Pin the report language so rendering assertions are deterministic. The report tests assert
# the Arabic (default) brand and section anchors; a developer running with REPORT_LANGUAGE=en
# in `.env` must not flip the suite to English output and break those assertions.
os.environ["REPORT_LANGUAGE"] = "ar"
