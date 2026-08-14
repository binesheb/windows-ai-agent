from __future__ import annotations

import hmac
import secrets
from pathlib import Path

TOKEN_DIR = Path.home() / "AppData" / "Local" / "WindowsAIAgent"
TOKEN_PATH = TOKEN_DIR / "auth.token"
TOKEN_BYTES = 32


def _create_token() -> str:
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(TOKEN_BYTES)
    TOKEN_PATH.write_text(token + "\n", encoding="utf-8")
    try:
        TOKEN_PATH.chmod(0o600)
    except OSError:
        pass
    return token


def get_or_create_token() -> str:
    if TOKEN_PATH.exists():
        token = TOKEN_PATH.read_text(encoding="utf-8").strip()
        if token:
            return token
    return _create_token()


def token_matches(candidate: str | None) -> bool:
    if not candidate:
        return False
    expected = get_or_create_token()
    return hmac.compare_digest(candidate, expected)


def token_path() -> str:
    return str(TOKEN_PATH)
