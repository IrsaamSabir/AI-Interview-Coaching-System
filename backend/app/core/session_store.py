from typing import Dict

SESSION_STORE: Dict[str, object] = {}

def create_session(session_id: str, session):
    """Save a new InterviewSession into the store."""
    SESSION_STORE[session_id] = session

def get_session(session_id: str):
    """Retrieve a session by ID. Returns None if not found."""
    return SESSION_STORE.get(session_id)

def delete_session(session_id: str):
    """Remove a session (call after report is delivered if you want cleanup)."""
    SESSION_STORE.pop(session_id, None) 

def list_sessions() -> list:
    """Return all active session IDs (useful for debugging)."""
    return list(SESSION_STORE.keys())