"""MCP bridge for the Windows AI Agent.

This bridge exposes the existing security-controlled read capabilities through
Model Context Protocol. It deliberately does not expose arbitrary command
execution or write/control operations.

Run locally with:
    python -m agent.mcp_server

The server listens on 127.0.0.1:8766 and uses the same local agent token as
the REST API, supplied as an MCP Bearer token.
"""

from __future__ import annotations

from typing import Any

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from pydantic import AnyHttpUrl

from agent.core.auth import token_matches
from agent.core.config import filesystem_settings, filesystem_workspaces
from agent.core.paths import evaluate_path
from agent.core.policy import PolicyEngine
from agent.system.filesystem import list_directory, read_text_file
from agent.system.inventory import get_system_inventory
from agent.system.services import get_service_inventory


MCP_HOST = "127.0.0.1"
MCP_PORT = 8766
MCP_RESOURCE_URL = f"http://{MCP_HOST}:{MCP_PORT}"


class LocalAgentTokenVerifier(TokenVerifier):
    """Validate the same locally generated secret used by the REST API."""

    async def verify_token(self, token: str) -> AccessToken | None:
        if not token_matches(token):
            return None
        return AccessToken(
            token=token,
            client_id="local-ai",
            scopes=["windows:read"],
        )


policy = PolicyEngine()

mcp = FastMCP(
    "Windows AI Agent",
    instructions=(
        "Security-first Windows computer access. Read-only MCP bridge. "
        "Never assume write or control capability exists; inspect policy "
        "before requesting an operation."
    ),
    stateless_http=True,
    json_response=True,
    token_verifier=LocalAgentTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://localhost.invalid"),
        resource_server_url=AnyHttpUrl(MCP_RESOURCE_URL),
        required_scopes=["windows:read"],
    ),
)

# FastMCP's current direct-execution API reads the bind settings from
# mcp.settings. Passing host/port to mcp.run() is not supported in the
# installed SDK version.
mcp.settings.host = MCP_HOST
mcp.settings.port = MCP_PORT


def _require(capability: str) -> None:
    decision = policy.evaluate(capability)
    if not decision.allowed:
        raise PermissionError(decision.reason)


@mcp.tool()
def get_system() -> dict[str, Any]:
    """Inspect basic Windows system health and hardware information."""
    _require("system_inventory")
    return get_system_inventory()


@mcp.tool()
def list_processes(limit: int = 250) -> dict[str, Any]:
    """List currently running processes without controlling them."""
    _require("process_read")
    from agent.main import get_process_inventory

    processes = get_process_inventory(limit)
    return {"count": len(processes), "processes": processes}


@mcp.tool()
def list_services(limit: int = 500) -> dict[str, Any]:
    """List Windows services without starting, stopping, or changing them."""
    _require("service_read")
    services = get_service_inventory(limit)
    return {"count": len(services), "services": services}


@mcp.tool()
def list_workspaces() -> dict[str, Any]:
    """Return configured filesystem workspaces and their access modes."""
    _require("filesystem_read")
    roots, _, _ = filesystem_settings()
    result = []
    for workspace in filesystem_workspaces():
        decision = evaluate_path(workspace["path"], roots)
        result.append(
            {
                "name": workspace["name"],
                "path": decision.normalized,
                "access": workspace["access"],
                "allowed": decision.allowed,
                "reason": decision.reason,
            }
        )
    return {"count": len(result), "workspaces": result}


@mcp.tool()
def list_directory(path: str = ".", limit: int = 500) -> dict[str, Any]:
    """List files and directories inside an authorized workspace."""
    _require("filesystem_read")
    roots, _, configured_limit = filesystem_settings()
    decision = evaluate_path(path, roots)
    if not decision.allowed:
        raise PermissionError(decision.reason)
    from pathlib import Path

    target = Path(decision.normalized)
    if not target.is_dir():
        raise ValueError("Path is not a directory")
    entries = list_directory(target, min(limit, configured_limit))
    return {"path": str(target), "count": len(entries), "entries": entries}


@mcp.tool()
def read_file(path: str) -> dict[str, Any]:
    """Read a text file inside an authorized workspace."""
    _require("filesystem_read")
    roots, max_read_bytes, _ = filesystem_settings()
    decision = evaluate_path(path, roots)
    if not decision.allowed:
        raise PermissionError(decision.reason)
    from pathlib import Path

    return read_text_file(Path(decision.normalized), max_read_bytes)


@mcp.tool()
def get_capabilities() -> dict[str, Any]:
    """Return the agent's current capability and policy state."""
    from agent.core.capabilities import all_capabilities

    result = []
    for item in all_capabilities():
        decision = policy.evaluate(str(item["name"]))
        result.append(
            {
                **item,
                "enabled": decision.allowed,
                "requires_approval": decision.requires_approval,
                "policy_reason": decision.reason,
            }
        )
    return {"capabilities": result}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
