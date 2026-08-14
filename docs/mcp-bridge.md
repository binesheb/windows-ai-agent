# ChatGPT / MCP Bridge

The Windows AI Agent exposes a separate Model Context Protocol (MCP) bridge for AI clients.

## Security model

- The bridge listens on `127.0.0.1:8766` only.
- It uses the same locally generated `WindowsAIAgent` token as the REST API.
- MCP clients authenticate with a Bearer token.
- Only read capabilities are exposed in the first bridge release.
- The existing policy engine remains authoritative.
- No arbitrary shell, PowerShell, filesystem write, process control, service control, Git, Docker, or network-control tool is exposed.

## Start the bridge

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m agent.mcp_server
```

The MCP endpoint is:

`http://127.0.0.1:8766/mcp`

## Available MCP tools

- `get_system`
- `list_processes`
- `list_services`
- `list_workspaces`
- `list_directory`
- `read_file`
- `get_capabilities`

## Token

The MCP bridge uses the same token stored locally at:

`%LOCALAPPDATA%\WindowsAIAgent\auth.token`

Never commit or paste the token into GitHub, issues, logs, or chat.

## ChatGPT connectivity

ChatGPT does not directly connect to a localhost MCP server. OpenAI's current guidance says remote MCP servers are used for custom apps; private/local servers should use the supported Secure MCP Tunnel rather than exposing the server publicly.

This repository therefore keeps the MCP bridge local and secure first. The tunnel/deployment layer is intentionally separate from the Windows control plane.

## Future write support

Write/control tools will not be added merely because the MCP transport exists. Each capability must remain disabled by default, pass the policy engine, and use the Windows AI Agent approval workflow where required.
