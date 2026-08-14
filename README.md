# Windows AI Agent

Security-first local control plane for AI-assisted interaction with a Windows computer.

## Vision

Give an AI useful access to a Windows machine without turning the computer into an unrestricted remote shell.

```text
AI / Codex
    |
    v
Windows AI Agent
    |
    +-- Authentication
    +-- Policy Engine
    +-- Capability Registry
    +-- Approval Manager
    +-- Audit Log
    |
    +-- System
    +-- Files
    +-- Processes
    +-- Services
    +-- PowerShell
    +-- Git
    +-- Docker
```

## Security principles

1. Localhost-only by default.
2. Read-only by default.
3. Every operation maps to a named capability.
4. Unknown capabilities are denied.
5. Sensitive operations require approval.
6. Dangerous operations require explicit confirmation and additional safeguards.
7. Secrets never belong in Git.
8. Security-relevant actions are audited.
9. A local kill switch will be available before privileged features are enabled.
10. GitHub is the source of truth for code and policy, not a credential store.

## Current release

**v0.1 — Foundation**

The first milestone provides a localhost API, system inventory, deny-by-default capability policy, audit logging, automated tests, and CI. It intentionally provides no arbitrary command execution.

## Development

Python 3.11+ is recommended.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn agent.main:app --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/docs` for the local API documentation.

## Repository structure

```text
agent/
  api/          API routes
  audit/        security audit logging
  core/         policy/capability core
  system/       Windows/system inspection
config/         runtime configuration
policies/       capability policy
docs/           architecture and security documentation
tests/          automated tests
.github/        CI automation
```

## Roadmap

- [x] Secure repository foundation
- [x] Local read-only API
- [x] System inventory
- [x] Deny-by-default policy engine
- [x] Audit logging
- [x] Automated tests and CI
- [ ] Capability registry
- [ ] Authentication
- [ ] Approval workflow
- [ ] Filesystem read capability
- [ ] Process inspection
- [ ] Windows service inspection
- [ ] Controlled process/service operations
- [ ] Sandboxed PowerShell execution
- [ ] Git integration
- [ ] Docker integration
- [ ] Windows service installer
- [ ] Secure outbound remote-control channel
- [ ] Desktop approval UI
- [ ] Multi-machine management

## Contribution

Ideas, issues, security reviews, pull requests, and forks are welcome. Security-sensitive changes should be reviewed carefully before merging.

See `SECURITY.md` and `CONTRIBUTING.md`.