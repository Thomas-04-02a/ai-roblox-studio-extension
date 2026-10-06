import secrets
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class SessionRecord:
    session_id: str
    token: str
    created_at: float
    last_seen: float
    provider: Optional[str] = None
    status: str = "idle"
    tool_calls: int = 0


class SessionManager:
    _sessions: Dict[str, SessionRecord] = {}
    _lock = threading.RLock()

    @classmethod
    def create_session(cls, provider: str = "unknown") -> SessionRecord:
        session_id = secrets.token_urlsafe(24)
        token = secrets.token_urlsafe(32)
        now = time.time()
        record = SessionRecord(
            session_id=session_id,
            token=token,
            created_at=now,
            last_seen=now,
            provider=provider,
            status="idle",
            tool_calls=0,
        )
        with cls._lock:
            cls._sessions[session_id] = record
        return record

    @classmethod
    def validate_token(cls, session_id: str, token: str) -> bool:
        with cls._lock:
            record = cls._sessions.get(session_id)
            if record is None:
                return False
            if record.token != token:
                return False
            record.last_seen = time.time()
            return True

    @classmethod
    def update_status(cls, session_id: str, status: str) -> bool:
        with cls._lock:
            record = cls._sessions.get(session_id)
            if record is None:
                return False
            record.status = status
            record.last_seen = time.time()
            return True

    @classmethod
    def add_tool_call(cls, session_id: str) -> bool:
        with cls._lock:
            record = cls._sessions.get(session_id)
            if record is None:
                return False
            record.tool_calls += 1
            record.last_seen = time.time()
            return True

    @classmethod
    def get_session(cls, session_id: str) -> Optional[SessionRecord]:
        with cls._lock:
            return cls._sessions.get(session_id)
