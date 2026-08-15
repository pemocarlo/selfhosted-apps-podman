# Manual operation

This guide operates the same rootless Podman Quadlets used by
`scripts/selfhosted`, but shows each layer explicitly. Run the commands as the
deployment user, from the repository root, on the VPS.

The repository contains definitions. Runtime state is created separately:

```text
repository/gateway/quadlet/*.container       source definitions
repository/services/<app>/quadlet/*          source definitions
~/selfhosted/gateway/                        Caddy config, env, certificates
~/selfhosted/services/<app>/                 env files and app data
~/.config/containers/systemd/                installed Quadlet definitions
```

A `.container` file is read by the Podman Quadlet generator and becomes a
user-systemd `.service` unit. A `.network` file creates a Podman network. The
service manager owns the container lifecycle; use `systemctl --user` for
start, stop, restart, and status. Use `podman` for inspection, image pulls,
and application-specific commands.

Never put real env files, credentials, databases, uploads, certificates, or
backups in the repository. The commands below preserve existing runtime files
when copying templates.

## First-time host setup

The deployment user needs a user systemd manager that survives logout. An
administrator enables lingering once, and the deployment user checks the
environment:

```sh
sudo loginctl enable-linger "$USER"
podman info --format '{{.Host.CgroupsVersion}}'
systemctl --user show-environment >/dev/null
```

The first command requires administrator access. Quadlets require cgroup v2.
For production ports 80 and 443, also configure the low-port sysctl described
in the root [README](../README.md), or use a different published port.

Set two useful paths once per shell. The defaults are the paths used by this
repository and by the helper script:

```sh
STATE="${SELFHOSTED_ROOT:-$HOME/selfhosted}"
UNIT_DIR="${QUADLET_DIR:-$HOME/.config/containers/systemd}"
```

## Gateway lifecycle

The gateway is one Caddy container plus the shared `caddy-public` network. It
reads `Caddyfile`, the `conf.d/*.caddy` route files, and `caddy.env` from
`$STATE/gateway`. App containers join the same Podman network; Caddy reaches
them by their container names, such as `grocy` or `bookstack`.

### Install a local gateway

Local mode publishes Caddy only on `127.0.0.1:8080`, so it is useful for a
first test without exposing the host publicly.

```sh
install -d "$STATE/gateway"/{conf.d,site,data,config} "$UNIT_DIR"
install -m 0644 gateway/Caddyfile "$STATE/gateway/Caddyfile"
cp -a gateway/conf.d/. "$STATE/gateway/conf.d/"
cp -a gateway/site/. "$STATE/gateway/site/"
test -e "$STATE/gateway/caddy.env" || \
  install -m 0600 gateway/caddy.example.env "$STATE/gateway/caddy.env"

install -m 0644 gateway/quadlet/caddy-public.network "$UNIT_DIR/"
install -m 0644 gateway/quadlet/caddy-local.container \
  "$UNIT_DIR/caddy-static.container"
systemctl --user daemon-reload
systemctl --user restart caddy-static.service
curl -I http://localhost:8080
```

The `daemon-reload` makes systemd run the Quadlet generator again. The
`restart` then creates or replaces the container from the generated service.
If the service has never run, `start` is equivalent; `restart` is convenient
after a definition or configuration change.

### Switch the gateway to production

Set the production hostnames in the runtime env file, make DNS point to this
server, and check the firewall before switching the published ports:

```sh
nano "$STATE/gateway/caddy.env"
install -m 0644 gateway/quadlet/caddy-production.container \
  "$UNIT_DIR/caddy-static.container"
systemctl --user daemon-reload
systemctl --user restart caddy-static.service
```

Changing a hostname in `caddy.env` or a route in `conf.d/` changes Caddy
configuration, not the app container. Copy the changed file into
`$STATE/gateway`, validate it, and restart only `caddy-static.service`:

```sh
podman run --rm --env-file "$STATE/gateway/caddy.env" \
  -v "$STATE/gateway/Caddyfile:/etc/caddy/Caddyfile:ro,Z" \
  -v "$STATE/gateway/conf.d:/etc/caddy/conf.d:ro,Z" \
  docker.io/library/caddy:2.11.4-alpine \
  caddy validate --config /etc/caddy/Caddyfile
systemctl --user restart caddy-static.service
```

Check the gateway and its network with:

```sh
systemctl --user status caddy-static.service
journalctl --user -u caddy-static.service -n 100 --no-pager
podman ps --filter name=caddy-static
podman network inspect caddy-public
```

## App lifecycle

For a simple app, the manual install is just: create its persistent
directories, copy its env template once, install its Quadlet, reload systemd,
and restart its service. Grocy is the smallest example:

```sh
APP=grocy
APP_STATE="$STATE/services/$APP"
install -d "$APP_STATE/config" "$UNIT_DIR"
test -e "$APP_STATE/grocy.env" || \
  install -m 0600 "services/$APP/grocy.example.env" "$APP_STATE/grocy.env"
nano "$APP_STATE/grocy.env"

install -m 0644 "services/$APP/quadlet/grocy.container" "$UNIT_DIR/"
systemctl --user daemon-reload
systemctl --user restart grocy.service
```

`PUID`, `PGID`, and `TZ` are read by the container at startup. The `config`
directory is mounted from the host, so replacing the container does not erase
Grocy's application data.

The service name comes from the Quadlet filename: `grocy.container` becomes
`grocy.service`; `bookstack-db.container` becomes
`bookstack-db.service`.

### Common app layouts

| App | User-systemd services | Persistent state | Important lifecycle detail |
| --- | --- | --- | --- |
| `grocy` | `grocy.service` | `services/grocy/config` | Restart after image updates; visit the root page once for migrations. |
| `bookstack` | `bookstack-db.service`, `bookstack.service` | `mysql`, `public-uploads`, `storage-uploads` | The app requires the private MySQL service. Back up the database and uploads together. |
| `artifactory` | `artifactory.service` | `services/artifactory/var` | Resource-heavy; back up before updating the floating image tag. |
| `conan-server` | `conan-server.service` | `server.conf`, `services/conan-server/data` | Uses a locally built image; restart after editing `server.conf`. |
| `hello-app` | `hello-api.service`, `hello-web.service` | none in this example | Build both local images; the web service depends on the API. |

The service READMEs contain app-specific variables and initialization steps.
The following commands show the lifecycle differences without hiding them
behind the helper:

```sh
# BookStack: install all definitions, then let the dependency start MySQL first.
install -m 0644 services/bookstack/quadlet/* "$UNIT_DIR/"
systemctl --user daemon-reload
systemctl --user restart bookstack-db.service bookstack.service

# Hello App: build images in its separate source repository, then restart both.
podman image exists localhost/hello-api:latest
podman image exists localhost/hello-web:latest
systemctl --user restart hello-api.service hello-web.service

# Conan Server: the image is local, so pull is not the update operation.
podman image exists localhost/conan-server:2.30.0
systemctl --user restart conan-server.service
```

## The basic lifecycle commands

Use systemd as the owner of Quadlet-created containers. A direct
`podman stop` may be immediately undone by `Restart=always`; it is useful for
diagnostics, but it is not the normal stop operation.

```sh
# Start, stop, or restart without changing the image.
systemctl --user start grocy.service
systemctl --user stop grocy.service
systemctl --user restart grocy.service

# Check state and recent logs.
systemctl --user status grocy.service
journalctl --user -u grocy.service -n 100 --no-pager
journalctl --user -u grocy.service -f

# Inspect the container and its logs when systemd details are not enough.
podman ps --filter name=grocy
podman inspect grocy
podman logs --tail 100 grocy
```

Stop following logs with `Ctrl-C`. It stops the log viewer, not the service.
For BookStack, include both units when investigating startup:

```sh
systemctl --user status bookstack-db.service bookstack.service
journalctl --user -u bookstack-db.service -u bookstack.service -n 150 --no-pager
```

### Configuration changes versus image updates

There are two different operations:

1. A configuration or Quadlet change: copy the changed file, run
   `daemon-reload`, then restart the affected unit.
2. An image update: pull the image, then restart the affected unit so the new
   image is used. Pulling alone does not replace a running container.

Examples:

```sh
# Quadlet definition changed.
install -m 0644 services/grocy/quadlet/grocy.container "$UNIT_DIR/"
systemctl --user daemon-reload
systemctl --user restart grocy.service

# Registry image changed.
podman pull lscr.io/linuxserver/grocy:latest
systemctl --user restart grocy.service
```

For BookStack, update the database and app images only after a consistent
backup. For Artifactory, review the vendor release notes first. For local
images (`hello-app` and `conan-server`), rebuild/tag the image and restart;
`podman pull` is intentionally skipped.

### Disable, remove, and restore

Manual disable is reversible: stop the service and remove only its installed
Quadlet definitions. Do not remove `$STATE/services/<app>`.

```sh
systemctl --user stop grocy.service
rm -f "$UNIT_DIR/grocy.container"
systemctl --user daemon-reload
```

To restore it, copy the definition again, reload, and start it:

```sh
install -m 0644 services/grocy/quadlet/grocy.container "$UNIT_DIR/"
systemctl --user daemon-reload
systemctl --user start grocy.service
```

Quadlet services are generated/transient from the definition files. Do not
use `systemctl --user enable` for these units; the `[Install]` section in the
Quadlet is applied by the generator during `daemon-reload`. Removing a
Quadlet definition removes the service definition, not the container image,
named network, or bind-mounted data.

There is no routine manual `remove` command that deletes app data. If data
must eventually be erased, verify a tested backup, stop the app, identify the
exact paths in its service README, and remove only those paths as a separate,
deliberate operation.

## What the helper simplifies

The helper is a safe convenience layer, not a different deployment model:

| Helper command | Manual equivalent |
| --- | --- |
| `scripts/selfhosted deploy gateway local` | Sync gateway files, install the local Quadlets, validate Caddy, reload, restart Caddy. |
| `scripts/selfhosted deploy <app>` | Create missing env/data paths, reject placeholders, install the app Quadlets, reload, restart its service(s). |
| `scripts/selfhosted restart <app>` | `systemctl --user restart <app>.service` (or all units listed in that app's `quadlet/` directory). |
| `scripts/selfhosted update <app>` | Pull registry images from the Quadlets, then restart that app's service(s). |
| `scripts/selfhosted disable <app>` | Stop the app, remove its managed Quadlets, and leave a disabled marker so `deploy all` skips it. |
| `scripts/selfhosted remove <app>` | Remove managed Quadlets and the disabled marker, while preserving runtime config and data. |

The helper tracks the Quadlet files it installed so it can remove obsolete
managed definitions without touching manually installed definitions or runtime
data. `deploy all` updates the gateway and previously installed apps; it does
not unexpectedly install every available app.

## Direct SSH and automated deployment

The GitHub workflow requires direct network connectivity from the GitHub
runner to the VPS. It performs two SSH-based operations:

1. `rsync` copies the repository definitions while excluding real env files.
2. A new `ssh` session runs `scripts/selfhosted <operation> <target>` on the
   VPS.

There is no jump host or tunnel configured. To operate manually, connect to
the VPS first and run the commands in this guide:

```sh
ssh -p "$PORT" "$USER@$HOST"
cd ~/selfhosted-infra
scripts/selfhosted status all
```

The helper is also useful over SSH because it keeps the remote command short:

```sh
ssh -p "$PORT" "$USER@$HOST" \
  'cd ~/selfhosted-infra && scripts/selfhosted restart grocy'
```

## Routine VPS health check

This is the read-only check sequence used to inspect a VPS over SSH. Set
`SSH_HOST` to the local SSH alias or hostname and replace the two example
domains with the sites that should currently be public.

The first command checks the host, rootless Podman, user systemd, repository
state, services, containers, and the shared network:

```sh
SSH_HOST=your-vps-alias
ssh "$SSH_HOST" 'cd ~/selfhosted-infra
id
hostname
uname -sr
podman --version
podman info --format "cgroups={{.Host.CgroupsVersion}} rootless={{.Host.Security.Rootless}}"
systemctl --user is-system-running
systemctl --user show-environment >/dev/null && echo user-systemd-available
scripts/selfhosted list
scripts/selfhosted status all
podman ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
podman network inspect caddy-public --format "{{.Name}} containers={{len .Containers}}"
'
```

Healthy output should show `cgroups=v2`, `rootless=true`, a running user
systemd manager, active services, and the expected number of containers on
`caddy-public`. Apps that have never been installed appear as `available` or
`not fully installed`; that is normal.

Run repository, Quadlet, and Caddy validation separately when needed:

```sh
ssh "$SSH_HOST" 'cd ~/selfhosted-infra && scripts/selfhosted check'
```

This does not restart services or alter application data. If the validation
image is not already cached, Podman may download the pinned Caddy image first.

Validate the deployed Caddy configuration directly and check the public
endpoints. A plain HTTP request normally returns `301` because it redirects to
HTTPS; the command below follows that redirect and should end with the
application response, commonly `200`:

```sh
ssh "$SSH_HOST" 'podman exec caddy-static caddy validate --config /etc/caddy/Caddyfile
awk -F= "/^[A-Za-z0-9_]+_SITE_ADDRESS=/ {print \$1 \"=\" \$2}" "$HOME/selfhosted/gateway/caddy.env"
for host in grocy.example.com bookstack.example.com; do
  curl -fsS -L -o /dev/null -w "$host %{http_code} ssl=%{ssl_verify_result}\n" \
    --max-time 20 "https://$host"
done'
```

`ssl=0` means curl trusted the certificate. Use `curl -k` only when
diagnosing a certificate problem; it deliberately skips certificate
verification.

Check failed user units, listeners, and resource pressure:

```sh
ssh "$SSH_HOST" 'systemctl --user --failed --no-legend || true
ss -lntup | awk "NR==1 || /:80 |:443 /"
df -h "$HOME" | tail -n 1
free -h | awk "NR==1 || NR==2"
podman system df'
```

No output from `systemctl --user --failed` is the healthy result. Production
Caddy should listen on TCP 80, TCP 443, and UDP 443. Keep an eye on disk space,
memory, and image/container storage before updates.

## Troubleshooting order

Check from the inside out:

```sh
# 1. Did systemd generate and start the service?
systemctl --user status grocy.service
systemctl --user cat grocy.service

# 2. Did the container start and join the expected network?
podman ps -a --filter name=grocy
podman inspect grocy
podman network inspect caddy-public

# 3. Is the gateway healthy and configured for the hostname?
systemctl --user status caddy-static.service
journalctl --user -u caddy-static.service -n 100 --no-pager

# 4. Does the local HTTP request reach Caddy?
curl -v -H 'Host: grocy.localhost' http://127.0.0.1:8080/
```

For a missing or invalid generated unit, run:

```sh
systemctl --user daemon-reload
systemd-analyze --user --generators=true verify grocy.service
systemctl --user cat grocy.service
```

For an unreachable production site, check the hostname in
`$STATE/gateway/caddy.env`, DNS, firewall ports 80/443 (including UDP 443 for
HTTP/3), the Caddy logs, and the upstream container name. Keep the VPS clock
correct because Caddy stores certificates under `$STATE/gateway/data`.

### High CPU or memory usage

Use the canonical [resource-pressure workflow](operations.md#detecting-high-cpu-or-memory-usage)
for the layered host, systemd, container, process, and log checks. For
Artifactory-specific interpretation and optional endpoint guidance, see the
[Artifactory operations runbook](../services/artifactory/OPERATIONS.md).

## Backups

Back up runtime state, not generated containers or images:

```text
~/selfhosted/gateway/{data,config,caddy.env}
~/selfhosted/services/<app>/
```

For database-backed apps, stop the relevant app or use its database-native
backup tool for a consistent snapshot. Test a restore before relying on a
backup.
Artifactory uses a rootless `:U` volume; its
[detailed operations runbook](../services/artifactory/OPERATIONS.md) documents
the required `podman unshare` backup and restore workflow.
