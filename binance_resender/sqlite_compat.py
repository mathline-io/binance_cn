import importlib
import os
import sys
from typing import Tuple


# Django 6 recommends SQLite >= 3.31.0. If system sqlite is older, we can
# transparently swap in pysqlite3-binary without patching Django source code.
MIN_SQLITE_VERSION: Tuple[int, int, int] = (3, 31, 0)


def _parse_version(version_text: str) -> Tuple[int, int, int]:
    parts = []
    for token in version_text.split("."):
        try:
            parts.append(int(token))
        except ValueError:
            break
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def patch_sqlite_for_django() -> bool:
    force_patch = os.getenv("RESENDER_FORCE_PYSQLITE3", "0") == "1"

    try:
        import sqlite3
    except Exception:
        sqlite3 = None

    current_version = (0, 0, 0)
    if sqlite3 is not None:
        version_text = getattr(sqlite3, "sqlite_version", "")
        current_version = _parse_version(version_text)

    needs_patch = force_patch or sqlite3 is None or current_version < MIN_SQLITE_VERSION
    if not needs_patch:
        return False

    try:
        pysqlite3 = importlib.import_module("pysqlite3")
    except Exception:
        return False

    sys.modules["sqlite3"] = pysqlite3
    if hasattr(pysqlite3, "dbapi2"):
        sys.modules["sqlite3.dbapi2"] = pysqlite3.dbapi2
    return True
