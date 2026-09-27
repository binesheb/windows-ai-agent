# Binesh AI Bootstrap Agent

`tools/binesh-bootstrap.ps1` prepares a Windows machine for local Binesh AI development.

## What it does

- Detects Windows, PowerShell, RAM, CPU and GPU.
- Installs Ollama through `winget` when it is missing.
- Starts/verifies the local Ollama service.
- Selects a model based on available system RAM, unless `-Model` is supplied.
- Pulls the selected model.
- Runs a real inference probe.
- Creates the repository Python virtual environment.
- Installs Python dependencies.
- Compiles the agent source.
- Writes a machine-readable `agent-report.json`.
- Exits non-zero when a required step fails.

## Run

From a clone of this repository:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\tools\binesh-bootstrap.ps1
```

For an explicit model:

```powershell
.\tools\binesh-bootstrap.ps1 -Model qwen3:8b
```

To rerun diagnostics without downloading a model:

```powershell
.\tools\binesh-bootstrap.ps1 -SkipModelPull
```

## Safety

The bootstrap does not enable arbitrary remote command execution. It only performs the documented local setup actions and records the result. Privileged or destructive capabilities remain outside the bootstrap.

## Feedback contract

The bootstrap produces `agent-report.json` using the `binesh-agent-report/v1` schema. A future controller can consume this report automatically without scraping console output.

Direct machine-to-ChatGPT feedback is intentionally not enabled by default; it requires an explicitly configured bridge/connector.
