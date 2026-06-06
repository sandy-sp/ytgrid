import os
import aiosqlite
from ytgrid.utils.config import config
from ytgrid.utils.logger import log_info, log_error

# Database path is configurable via YTGRID_DB_PATH (see Config.DB_PATH).
DB_PATH = config.DB_PATH
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


async def init_db():
    """Create the database (with WAL journaling) and apply the schema."""
    log_info(f"Initializing database at {DB_PATH}")

    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        # WAL allows concurrent readers alongside a writer — needed under API load.
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA foreign_keys = ON;")
        try:
            with open(SCHEMA_PATH, "r") as f:
                schema_sql = f.read()
            await db.executescript(schema_sql)
            await db.commit()
            log_info("Database schema initialized successfully.")
        except Exception as e:
            log_error(f"Failed to initialize database schema: {e}")


def get_db_path() -> str:
    return DB_PATH
