import aiosqlite
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from ytgrid.database import get_db_path


class ProfileRepository:
    def __init__(self):
        self.db_path = get_db_path()

    @asynccontextmanager
    async def _connect(self):
        """Yield a connection with foreign-key enforcement enabled.

        SQLite enforces foreign keys per-connection, so ON DELETE CASCADE
        only fires when this PRAGMA is set on the active connection.
        """
        db = await aiosqlite.connect(self.db_path)
        try:
            await db.execute("PRAGMA foreign_keys = ON;")
            yield db
        finally:
            await db.close()

    async def create_profile(self, name: str, description: Optional[str] = None) -> int:
        async with self._connect() as db:
            cursor = await db.execute(
                "INSERT INTO profiles (name, description) VALUES (?, ?)",
                (name, description),
            )
            await db.commit()
            return cursor.lastrowid

    async def list_profiles(self) -> List[Dict[str, Any]]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM profiles ORDER BY name ASC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_profile(self, identifier: Any) -> Optional[Dict[str, Any]]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            if isinstance(identifier, int):
                cursor = await db.execute(
                    "SELECT * FROM profiles WHERE id = ?", (identifier,)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM profiles WHERE name = ?", (identifier,)
                )
            row = await cursor.fetchone()
            if not row:
                return None
            profile = dict(row)

            cursor = await db.execute(
                "SELECT * FROM profile_entries WHERE profile_id = ? ORDER BY sequence_order ASC",
                (profile["id"],),
            )
            entries = await cursor.fetchall()
            profile["entries"] = [dict(e) for e in entries]
            return profile

    async def add_entry(
        self,
        profile_id: int,
        video_url: str,
        speed: float = 1.0,
        loop_count: int = 1,
    ) -> int:
        async with self._connect() as db:
            # Determine the next sequence number for this profile.
            cursor = await db.execute(
                "SELECT MAX(sequence_order) AS max_seq FROM profile_entries WHERE profile_id = ?",
                (profile_id,),
            )
            row = await cursor.fetchone()
            seq = (row[0] or 0) + 1

            cursor = await db.execute(
                "INSERT INTO profile_entries "
                "(profile_id, video_url, speed, loop_count, sequence_order) "
                "VALUES (?, ?, ?, ?, ?)",
                (profile_id, video_url, speed, loop_count, seq),
            )
            await db.commit()
            return cursor.lastrowid

    async def delete_profile(self, profile_id: int) -> bool:
        async with self._connect() as db:
            # ON DELETE CASCADE handles entries (foreign_keys enabled in _connect).
            cursor = await db.execute(
                "DELETE FROM profiles WHERE id = ?", (profile_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def record_execution_start(
        self, session_id: str, profile_id: Optional[int] = None
    ) -> int:
        async with self._connect() as db:
            cursor = await db.execute(
                "INSERT INTO execution_history (session_id, profile_id, status) "
                "VALUES (?, ?, ?)",
                (session_id, profile_id, "playing"),
            )
            await db.commit()
            return cursor.lastrowid

    async def record_execution_end(
        self, session_id: str, status: str, error_message: Optional[str] = None
    ) -> None:
        async with self._connect() as db:
            await db.execute(
                "UPDATE execution_history "
                "SET status = ?, completed_at = CURRENT_TIMESTAMP, error_message = ? "
                "WHERE session_id = ?",
                (status, error_message, session_id),
            )
            await db.commit()

    async def get_history(self, profile_id: int) -> List[Dict[str, Any]]:
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM execution_history WHERE profile_id = ? "
                "ORDER BY started_at DESC",
                (profile_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
