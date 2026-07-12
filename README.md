# Self-hosted Apps with Podman and Caddy

Run independent apps as rootless Podman 5.8 Quadlets behind one Caddy 2.11 gateway. App source and image builds belong in their own repositories.

## Requirements

- A Linux VPS with Podman 5.8 or newer, cgroup v2, and user systemd
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

Test locally first. This installs the shared gateway, then one app:

```sh
scripts/selfhosted deploy gateway local
curl -I http://localhost:8080
scripts/selfhosted list
scripts/selfhosted deploy grocy
# Open http://grocy.localhost:8080
```

For production, edit the generated hostnames, point DNS at the VPS, then switch profiles:

```sh
nano ~/selfhosted/gateway/caddy.env
scripts/selfhosted deploy gateway production
```

Apps with secrets stop on their first deploy after creating mode-`0600` env files. Edit the reported files and rerun the same command; existing env files and runtime data are never overwritten.

## Available apps

| Name | Purpose | Before the first deploy |
| --- | --- | --- |
| `grocy` | Household inventory | Review user IDs and timezone |
| `bookstack` | Wiki with a private MySQL database | Generate secrets and set its exact public URL |
| `artifactory` | Full Conan repository with web UI | Confirm the VPS meets Artifactory's substantial resource needs |
| `conan-server` | Small, basic Conan remote | Build its local image and create server secrets |
| `hello-app` | Example frontend and API | Build both local images |

Each service README contains only its extra setup, data paths, and backup notes. For a Conan remote, use Artifactory for a team-facing installation; `conan-server` is mainly a lightweight test or small trusted-team option.

## Everyday commands

```sh
scripts/selfhosted list                    # show available/installed/disabled apps
scripts/selfhosted deploy <name>           # install or re-enable one app
scripts/selfhosted add <name>              # explicit alias for first installation
scripts/selfhosted enable <name>           # re-enable a disabled/removed app
scripts/selfhosted restart <name|gateway>  # restart without pulling an image
scripts/selfhosted update <name|gateway>   # pull and restart one component
scripts/selfhosted update all              # update every enabled component
scripts/selfhosted disable <name>           # temporary stop; preserve all data
scripts/selfhosted remove <name>            # uninstall units; preserve config/data
scripts/selfhosted status [name|gateway|all]
scripts/selfhosted logs <name|gateway>      # show the last 100 journal lines
scripts/selfhosted logs <name> --follow     # follow live logs; stop with Ctrl-C
scripts/selfhosted check                    # validate the host and configuration
```

`deploy all [local|production]` deploys the gateway and previously installed apps. New and disabled apps require an explicit `deploy <name>`.

`list` reports `available` (not installed), `configured` (runtime files exist but Quadlets are not installed), `installed`, `needs-deploy` (repository definitions changed), or `disabled`. A common `configured` state is the first deploy of an app with secret placeholders; edit the generated file and repeat the deploy. For `needs-deploy`, run `scripts/selfhosted deploy <name>`.

`disable` remembers that an app must stay off, so `deploy all` skips it. `remove` forgets that disabled state and removes only its managed systemd/Podman definitions; its environment files and persistent directories remain in `~/selfhosted`. Use `enable <name>` or `deploy <name>` to bring either state back. There is deliberately no automatic data-deletion command.

## Where files live

```text
repository/                         version-controlled definitions
~/selfhosted/                       env files and persistent runtime data
~/.config/containers/systemd/       installed rootless Quadlets
```

Never commit real env files, credentials, keys, databases, uploads, or backups. Commit only sanitized env templates.

See [manual installation](docs/manual.md) for direct Podman/systemd commands, [adding a service](docs/adding-a-service.md) for the repository pattern, and [operations](docs/operations.md) for maintenance.

## Optional GitHub deployment

The included workflow deploys over SSH. Configure the `production` environment with secrets `VPS_HOST`, `VPS_USER`, `VPS_PORT`, `VPS_SSH_KEY`, and trusted `VPS_KNOWN_HOSTS`. `VPS_DEPLOY_PATH` defaults to `selfhosted-infra`. Complete the first deployment on the VPS to create and edit runtime env files.

Use a dedicated Ed25519 key and verify the host key independently. Protect the GitHub environment with required reviewers when appropriate.

## Add an app

Follow [adding a service](docs/adding-a-service.md). New services are not started by `deploy all` until deployed explicitly once.
