# Self-hosted Apps with Podman and Caddy

Run independent apps as rootless Podman 5.8 Quadlets behind one Caddy 2.11 gateway. App source and image builds belong in their own repositories.

## Requirements

- A Linux VPS with Podman 5.8.x, cgroup v2, and user systemd
- A non-root deployment user with lingering enabled
- DNS records pointing each production hostname to the VPS
- Inbound TCP `80`/`443` and UDP `443` allowed

One-time host setup (the first two commands require an administrator):

```sh
sudo loginctl enable-linger "$USER"
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80
# Make the sysctl persistent using your distribution's /etc/sysctl.d mechanism.

git clone <repository-url> ~/selfhosted-infra
cd ~/selfhosted-infra
scripts/selfhosted check
```

The low-port sysctl lets the rootless gateway bind ports 80 and 443. If your provider redirects high ports instead, adjust the production Quadlet and omit it.

## Quick start

Test locally first:

```sh
scripts/selfhosted deploy gateway local
curl -I http://localhost:8080
scripts/selfhosted list
scripts/selfhosted deploy app grocy
```

For production, edit the generated hostnames, point DNS at the VPS, then switch profiles:

```sh
nano ~/selfhosted/gateway/caddy.env
scripts/selfhosted deploy gateway production
```

Apps with secrets stop on their first deploy after creating mode-`0600` env files. Edit the reported files and rerun the same command; existing env files and runtime data are never overwritten.

## Everyday commands

```sh
scripts/selfhosted deploy app <name>       # install or re-enable one app
scripts/selfhosted update <name|gateway>   # pull and restart one component
scripts/selfhosted update all              # update every enabled component
scripts/selfhosted disable <name>           # stop app; preserve all data
scripts/selfhosted status [name|gateway|all]
scripts/selfhosted check
```

`deploy all [local|production]` deploys the gateway and all enabled apps. A disabled app stays disabled until explicitly deployed.

## Where files live

```text
repository/                         version-controlled definitions
~/selfhosted/                       env files and persistent runtime data
~/.config/containers/systemd/       installed rootless Quadlets
```

Never commit real env files, credentials, keys, databases, uploads, or backups. Only sanitized `*.example.env`/`*.env.example` templates belong here.

See [operations](docs/operations.md) for manual operation, validation, troubleshooting, updates, and backups. Each service README documents only its settings and data paths.

## Optional GitHub deployment

The included workflow syncs this repository over SSH and runs the same helper. Configure the `production` environment with secrets `VPS_HOST`, `VPS_USER`, `VPS_PORT`, `VPS_SSH_KEY`, and trusted `VPS_KNOWN_HOSTS`; optionally set `VPS_DEPLOY_PATH` (default `selfhosted-infra`). Run the first deployment manually on the VPS so you can create and edit runtime env files. Protect the environment with required reviewers if desired.

Use a dedicated Ed25519 deployment key and obtain `known_hosts` from a connection you have independently verified. Repository secrets are never copied into runtime env files.

## Add an app

Add `services/<name>/quadlet/`, safe env templates, persistent-directory `.gitkeep` files, one route under `gateway/conf.d/`, and a short service README. Connect only the proxy-facing container to `caddy-public.network`; keep databases on a private app network.
