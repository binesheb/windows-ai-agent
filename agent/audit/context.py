from __future__ import annotations

from contextvars import ContextVar


_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_caller: ContextVar[str | None] = ContextVar("caller", default=None)


def set_request_context(request_id: str, caller: str | None = None) -> None:
    _request_id.set(request_id)
    _caller.set(caller)


def set_caller(caller: str) -> None:
    _caller.set(caller)


def get_request_id() -> str | None:
    return _request_id.get()


def get_caller() -> str | None:
    return _caller.get()
