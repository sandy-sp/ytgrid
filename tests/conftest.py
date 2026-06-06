import os
import sqlite3

import pytest

from ytgrid.database.repository import ProfileRepository

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ytgrid", "database", "schema.sql",
)


@pytest.fixture
def repo(tmp_path):
    """A ProfileRepository backed by a fresh temporary SQLite database."""
    db_file = tmp_path / "test_ytgrid.db"
    with sqlite3.connect(db_file) as con:
        with open(SCHEMA_PATH) as f:
            con.executescript(f.read())
    repository = ProfileRepository()
    repository.db_path = str(db_file)
    return repository
