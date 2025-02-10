# ytgrid/backend/dependencies.py
def get_session_store():
    """
    Returns the active session store.
    For now, we use the in-memory implementation.
    Later you can adjust this to select a multiprocessing-backed store
    based on configuration.
    """
    from ytgrid.backend.session_store import InMemorySessionStore
    return InMemorySessionStore()
