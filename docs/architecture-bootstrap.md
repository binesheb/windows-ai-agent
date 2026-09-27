# Bootstrap Architecture

The bootstrap is deliberately separate from the agent's privileged control plane.

```text
bootstrap.ps1
    |
    +--> system discovery
    +--> Ollama installation/verification
    +--> model provisioning
    +--> inference health check
    +--> Python environment
    +--> agent source validation
    |
    +--> agent-report.json
```

The report is the hand-off contract between the Windows machine and an external controller. Future versions can add a signed outbound transport, but the default remains local-only.

## Failure behavior

Any required failure sets the report status to `failed`, records the error, prints the report location, and exits with code 1. Successful completion sets status to `ready` and exits with code 0.

## Model selection

The current conservative defaults are:

- below 12 GB RAM: `qwen3:4b`
- 12–23 GB RAM: `qwen3:8b`
- 24 GB RAM or more: `qwen3:14b`

Users can override the model with `-Model`.
