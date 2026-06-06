"""
Dependency Injection for YTGrid Backend (Version 3.1)

This module provides functions to obtain dependencies for the backend, such as a session store.
Currently, it returns an instance of InMemorySessionStore. Future enhancements may allow selection
between an in-memory store and a multiprocessing-backed store based on configuration.
"""

from ytgrid.backend.session_store import InMemorySessionStore

_store_instance = None

def get_session_store():
    """
    Returns the active singleton session store instance.
    """
    global _store_instance
    if _store_instance is None:
        _store_instance = InMemorySessionStore()
    return _store_instance
