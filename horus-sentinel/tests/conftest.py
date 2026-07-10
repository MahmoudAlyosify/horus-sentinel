"""Test configuration.

Point the relational store at a throwaway SQLite file *before* any application module
imports the engine, so tests never touch a developer's real database.
"""

import os
import tempfile

# Must run before `core.db` (and anything importing it) is first imported.
_TMP_DB = os.path.join(tempfile.gettempdir(), "horus_sentinel_test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TMP_DB}")
