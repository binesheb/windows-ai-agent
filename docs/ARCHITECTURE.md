# Architecture

## Trust boundaries

The Windows AI Agent is a local control plane. The AI is not granted direct operating-system privileges. Requests must enter through named capabilities and the policy engine.

```text
AI / Codex
   |
   | request
   v
Local Agent API
   |
   +--> authentication
   |
   +--> capability lookup
   |
   +--> policy evaluation
   |
   +--> approval (when required)
   |
   +--> executor
   |
   +--> audit
   v
Windows
```

## Initial network boundary

The agent binds to `127.0.0.1` only. No router port forwarding or public listener is required.

## Capability model

Capabilities are named actions such as `system_inventory`, `process_read`, `service_control`, and `powershell`. Unknown capabilities are denied. A capability may be enabled by policy but still require human approval based on risk.

## Evolution

Future remote control should use an authenticated outbound channel rather than exposing a raw administrative API. The remote protocol must preserve the same policy and audit boundary used locally.
