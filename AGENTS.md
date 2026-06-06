# Agent Instructions

## Scope

This repository deploys rootless Podman Quadlets and Caddy configuration. Keep application source code in its own repository.

## Rules

- Never commit real `.env` files, credentials, private keys, runtime data, or backups.
- Keep safe environment templates named `*.example.env`.
- Preserve manual Podman/systemd operation while maintaining `scripts/selfhosted` as the canonical automation path.
- A service must deploy, update, stop, and fail independently from unrelated services.
- Do not delete or overwrite runtime data during deploy or disable.
- Keep the root README authoritative. Service READMEs contain only service-specific configuration, tests, and backup paths.
- Validate shell syntax with `bash -n scripts/selfhosted`.
- Validate Quadlets and Caddy when Podman/systemd tooling is available.
