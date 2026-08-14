# Security Policy

## Threat model

This agent is designed to control a local Windows workstation on behalf of an authorized user. The primary security goal is to prevent an AI request, malicious input, compromised dependency, or remote caller from obtaining unrestricted control.

## Non-negotiable defaults

- Bind to `127.0.0.1` unless remote access is deliberately configured.
- Deny capabilities unless explicitly enabled.
- Never execute arbitrary shell commands in the base agent.
- Require approval for sensitive actions.
- Keep secrets outside the repository.
- Log security-relevant actions.
- Provide a local emergency disable mechanism.

## Sensitive capabilities

Examples include modifying services, firewall configuration, user accounts, protected files, software installation, and unrestricted PowerShell. These capabilities must have explicit policy entries and tests before implementation.

## Reporting vulnerabilities

Do not publish credentials, tokens, private keys, or an exploit against a real machine in an issue. Report security-sensitive defects privately to the repository owner and include reproduction steps, affected component, impact, and mitigation where possible.