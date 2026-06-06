# Self-hosted Apps with Podman Quadlets

Rootless Podman Quadlets run independent apps behind one Caddy gateway. Application source and image builds belong in separate repositories.

## Layout

- `gateway/`: shared Caddy gateway, public network, routes, and static landing page.
- `services/<name>/`: one independently deployable app or app group.
- `scripts/selfhosted`: canonical deploy, disable, update, and status commands.
- `.github/workflows/deploy.yml`: SSH deployment from GitHub Actions.
- `docs/operations.md`: manual install, troubleshooting, and maintenance.

Runtime configuration and data live outside Git:

```text
~/selfhosted/
  gateway/{caddy.env,data,config,...}
  services/<name>/{*.env,data-directories...}
~/.config/containers/systemd/
```

Real `*.env` files are ignored. Commit only sanitized `*.example.env` templates.

## Automated Operations

Run from repository root on the VPS:

```sh
# First deploy.
scripts/selfhosted deploy gateway production
scripts/selfhosted deploy app grocy
scripts/selfhosted deploy all production

# Independent lifecycle. Disable persists across deploy/update all.
scripts/selfhosted disable grocy
scripts/selfhosted deploy app grocy
scripts/selfhosted status grocy

# Pull configured registry images and restart only selected component.
scripts/selfhosted update grocy
scripts/selfhosted update all
```

Deployment creates missing env files from `*.example.env` with mode `0600`. It stops if an app env still contains `CHANGE_ME`; edit files under `~/selfhosted/services/<name>/`, then rerun. Existing env files are never overwritten. Edit generated `~/selfhosted/gateway/caddy.env` before public use. Disable creates a runtime `.disabled` marker; `deploy all` and `update all` skip marked apps, while explicit `deploy app <name>` re-enables one.

## GitHub Actions Deployment

Workflow syncs repository files over SSH, includes safe `*.example.env` templates, excludes runtime `*.env`, then runs `scripts/selfhosted`. Pushes to `main` deploy all with production gateway. Manual workflow runs can deploy, update, or disable one target.

1. Create a dedicated key:

```sh
ssh-keygen -t ed25519 -f ~/.ssh/github-actions-vps -C github-actions-vps
```

2. Add `~/.ssh/github-actions-vps.pub` to deployment user's `~/.ssh/authorized_keys` on VPS. Verify that user can run `systemctl --user`, Podman, and `loginctl enable-linger`.
3. Capture host key from a trusted connection:

```sh
ssh-keyscan -H your-vps.example.com
```

4. In GitHub repository `Settings > Secrets and variables > Actions`, add:

| Type     | Name              | Value                                            |
| -------- | ----------------- | ------------------------------------------------ |
| Secret   | `VPS_HOST`        | VPS hostname or IP                               |
| Secret   | `VPS_USER`        | rootless deployment user                         |
| Secret   | `VPS_PORT`        | SSH port, usually `22`                           |
| Secret   | `VPS_SSH_KEY`     | private key contents                             |
| Secret   | `VPS_KNOWN_HOSTS` | trusted `ssh-keyscan` output                     |
| Variable | `VPS_DEPLOY_PATH` | repository sync path, default `selfhosted-infra` |

5. Before first CI deploy, run deployment once on VPS, edit generated env files, and rerun. GitHub Actions cannot and should not upload secrets from this repository.
6. Protect the GitHub `production` environment if deployments require approval.

## Backups

Back up runtime data, not generated containers:

- `~/selfhosted/gateway/data` and `~/selfhosted/gateway/config`
- `~/selfhosted/services/*/` including env files and app data

Test restoration. Database-backed apps need consistent database backups before upgrades.

## Add an App

Add `services/<name>/quadlet/`, safe `*.example.env` templates, persistent-directory `.gitkeep` files, a route in `gateway/conf.d/`, and a short service README containing only app-specific settings, tests, and backup paths.
