import sqlite3


async def test_create_and_get_profile(repo):
    pid = await repo.create_profile("morning", "daily mix")
    assert isinstance(pid, int)
    profile = await repo.get_profile("morning")
    assert profile["name"] == "morning"
    assert profile["description"] == "daily mix"
    assert profile["entries"] == []


async def test_get_profile_by_id(repo):
    pid = await repo.create_profile("p1")
    profile = await repo.get_profile(pid)
    assert profile["id"] == pid


async def test_get_missing_profile(repo):
    assert await repo.get_profile("does-not-exist") is None


async def test_add_entry_sequence_order(repo):
    pid = await repo.create_profile("p")
    await repo.add_entry(pid, "https://youtube.com/watch?v=a")
    await repo.add_entry(pid, "https://youtube.com/watch?v=b", speed=2.0, loop_count=3)
    profile = await repo.get_profile(pid)
    entries = profile["entries"]
    assert len(entries) == 2
    assert entries[0]["sequence_order"] == 1
    assert entries[1]["sequence_order"] == 2
    assert entries[1]["speed"] == 2.0
    assert entries[1]["loop_count"] == 3


async def test_list_profiles_ordered_by_name(repo):
    await repo.create_profile("banana")
    await repo.create_profile("apple")
    names = [p["name"] for p in await repo.list_profiles()]
    assert names == ["apple", "banana"]


async def test_delete_profile_cascades_entries(repo):
    pid = await repo.create_profile("p")
    await repo.add_entry(pid, "https://youtube.com/watch?v=a")
    assert await repo.delete_profile(pid) is True
    assert await repo.get_profile(pid) is None
    # ON DELETE CASCADE must have removed the entries too.
    with sqlite3.connect(repo.db_path) as con:
        count = con.execute(
            "SELECT COUNT(*) FROM profile_entries WHERE profile_id = ?", (pid,)
        ).fetchone()[0]
    assert count == 0


async def test_delete_missing_profile(repo):
    assert await repo.delete_profile(9999) is False


async def test_execution_history_lifecycle(repo):
    pid = await repo.create_profile("p")
    await repo.record_execution_start("sess-1", pid)
    await repo.record_execution_end("sess-1", "completed")
    history = await repo.get_history(pid)
    assert len(history) == 1
    assert history[0]["session_id"] == "sess-1"
    assert history[0]["status"] == "completed"
    assert history[0]["completed_at"] is not None
