# Updating Windows AI Agent

Windows AI Agent is security-sensitive. Updates must come from the configured Git repository and must never overwrite uncommitted local changes.

## Manual update

From the repository root in PowerShell:

```powershell
.\tools\update.ps1
```

The updater fetches `origin/main`, refuses to continue when the working tree contains local changes, and only performs a fast-forward update.

To check without changing files:

```powershell
.\tools\update.ps1 -CheckOnly
```

## Automatic update

For unattended installations, schedule the same check-only command and only invoke the update command after the deployment owner has approved the target revision or release. Do not silently replace a running security-control process with arbitrary branch contents.

A production auto-update implementation should use signed, versioned GitHub Release artifacts, verify integrity before installation, stop the service cleanly, update, run a health check, and restart only after validation.

## After updating

Recreate or update the virtual environment dependencies if `requirements.txt` changed, then restart the local service using the deployment's normal launcher.

## Rollback

The updater deliberately does not force-reset history. If an update must be rolled back, stop the service and deploy a previously validated tagged release or commit through the normal Git workflow, then restart and verify the local health endpoint.

## Release policy

Use semantic versions. Patch releases are for compatible fixes and documentation/install improvements; minor releases add compatible capabilities; major releases are reserved for breaking API, policy, or deployment changes.
