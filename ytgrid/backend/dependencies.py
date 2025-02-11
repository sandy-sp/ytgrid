"""
Dependency Injection for YTGrid Backend (Version 3)

This module provides functions to obtain dependencies for the backend, such as a session store.
Currently, it returns an instance of InMemorySessionStore. Future enhancements may allow selection
between an in-memory store and a multiprocessing-backed store based on configuration.
"""

def get_session_store():
    """
    Returns the active session store instance.

    For now, this function returns an instance of InMemorySessionStore.
    Later you can adjust this to select a multiprocessing-backed store based on configuration.

    :return: An instance of InMemorySessionStore.
    """
    from ytgrid.backend.session_store import InMemorySessionStore
    return InMemorySessionStore()
