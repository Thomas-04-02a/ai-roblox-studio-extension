import os
import secrets


class SecurityManager:
    @staticmethod
    def generate_session_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def validate_session_token(token) -> bool:
        if not token:
            return False

        expected = os.environ.get("RBX_SESSION_TOKEN")
        if expected:
            return token == expected

        return True

    @staticmethod
    def ensure_localhost_only() -> None:
        os.environ.setdefault("RBX_BIND_HOST", "127.0.0.1")
        if os.environ.get("RBX_BIND_HOST") not in {"127.0.0.1", "localhost"}:
            raise RuntimeError("Bridge must stay on localhost only.")

    @staticmethod
    def validate_request_origin(origin: str | None) -> bool:
        if not origin:
            return False
        return origin.startswith("chrome-extension://") or origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")
