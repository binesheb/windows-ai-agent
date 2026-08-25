# Changelog

All notable changes to Windows AI Agent are documented here.

The project follows [Semantic Versioning](https://semver.org/). Release notes should describe security-relevant behavior, migration steps, and rollback considerations.

## [Unreleased]

### Changed
- Clarified the release history and version baseline for the security-first local control plane.

### Fixed
- Made the Windows test helper platform-neutral so the test suite can run on non-Windows CI runners without weakening the production Windows-only design intent.

## [0.5.1] - 2026-08-21

### Added
- Approval lifecycle and replay-protection test coverage.
- Python dependency bootstrap helper for reproducible local setup.

### Fixed
- Current FastMCP server bind configuration.

### Changed
- Safe manual update and rollback guidance for deployments.

## [0.1.0] - Initial foundation

- Localhost API and read-only system inventory.
- Deny-by-default capability policy.
- Authentication, approval primitives, audit logging, tests, and CI.
- No arbitrary command execution.
