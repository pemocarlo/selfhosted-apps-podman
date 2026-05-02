# Selfhosted Apps With Podman Quadlets

Infrastructure repository for self-hosted services managed with rootless Podman, systemd Quadlets, and a shared Caddy gateway.

This repo should contain deployment definitions, Caddy routes, runtime directory templates, and operational documentation. Application source code belongs in separate development repositories that publish container images.

## Repository Model

- `gateway/`: shared Caddy reverse proxy, automatic TLS, static landing page, and shared Podman network.
- `services/`: one directory per deployed service or app group.
- `services/hello-app/`: deployment metadata for the sibling `../hello-app` development repo images.
- `services/grocy/`: deployment metadata and persistent data template for Grocy.

The sibling `../hello-app` repository owns the FastAPI and React source code. This infrastructure repo only consumes its images, currently named `localhost/hello-api:latest` and `localhost/hello-web:latest` for local builds.

## Service Catalog

| Service | Host Example | Purpose | Details |
| --- | --- | --- | --- |
| Gateway | `hello.myhostname.com` | Caddy edge service, TLS, shared routing | `gateway/README.md` |
| Hello App | `myapp.myhostname.com` | React frontend plus FastAPI backend images | `services/hello-app/README.md` |
| Grocy | `grocy.myhostname.com` | Household inventory app | `services/grocy/README.md` |

## Runtime Layout

Runtime files are copied under the user home directory:

```text
~/selfhosted/
  gateway/
    Caddyfile
    caddy.env
    conf.d/
    data/
    config/
  services/
    grocy/
      grocy.env
      config/
```

Quadlets are installed under:

```text
~/.config/containers/systemd/
```

## Initial Server Setup

Install Podman with Quadlet support and verify user systemd works:

```sh
podman --version
systemctl --user status
```

Keep user services running after logout:

```sh
loginctl enable-linger "$USER"
```

Create the runtime root:

```sh
mkdir -p ~/selfhosted
```

If you use `podman compose` for development in app repos, start the Podman socket:

```sh
systemctl --user start podman.socket
```

## Gateway First

Deploy the gateway before app services. The gateway creates the shared `caddy-public` network and owns all public ports.

See `gateway/README.md` for gateway setup.

## Adding Services

Each service should include:

- `services/<name>/README.md`
- `services/<name>/quadlet/*.container`
- `services/<name>/*.env.example` if environment variables are needed
- `services/<name>/config/.gitkeep` or other persistent directory templates if needed
- One or more Caddy routes in `gateway/conf.d/*.caddy`

Generic deployment flow:

```sh
cp services/<name>/quadlet/*.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start <service>.service
systemctl --user enable <service>.service
systemctl --user restart caddy-static.service
```

For app services built elsewhere, update the Quadlet `Image=` line to point at the image produced by that app's development repo or registry.

## Ports And TLS

For normal public Caddy usage, open:

- TCP `80` for ACME HTTP-01 certificate challenges and HTTP-to-HTTPS redirects.
- TCP `443` for HTTPS.
- UDP `443` for HTTP/3, optional.

Port `80` is not strictly required, but avoiding it requires a different certificate strategy such as TLS-ALPN-01 on `443` or DNS-01 with a custom Caddy DNS provider build.

For rootless Podman low ports:

```sh
sudo sysctl net.ipv4.ip_unprivileged_port_start=80
printf 'net.ipv4.ip_unprivileged_port_start=80\n' | sudo tee /etc/sysctl.d/99-rootless-podman-low-ports.conf
sudo sysctl --system
```

If using firewalld:

```sh
sudo firewall-cmd --add-service=http --add-service=https --permanent
sudo firewall-cmd --reload
```

## Maintenance

List service state:

```sh
systemctl --user list-units '*caddy*' '*grocy*' '*hello*'
podman ps
```

Reload Quadlets after changing unit files:

```sh
systemctl --user daemon-reload
```

Restart the gateway after changing `gateway/Caddyfile`, `gateway/conf.d/*.caddy`, or `gateway/caddy.env`:

```sh
systemctl --user restart caddy-static.service
```

Restart one app after changing its image or environment:

```sh
systemctl --user restart <service>.service
```

Pull image updates manually when not relying on auto-update:

```sh
podman pull <image>
systemctl --user restart <service>.service
```

Inspect image and container metadata:

```sh
podman images
podman inspect <container>
```

## Logging

Systemd service logs:

```sh
journalctl --user -u caddy-static.service -f
journalctl --user -u <service>.service -f
```

Container logs:

```sh
podman logs caddy-static
podman logs <container>
```

Recent boot logs for all user services:

```sh
journalctl --user -b
```

Show failed user units:

```sh
systemctl --user --failed
```

## Debugging

Check generated Quadlet units:

```sh
systemctl --user cat <service>.service
```

Validate Caddy config from this repo:

```sh
podman run --rm \
  -e SITE_ADDRESS=http://localhost:80 \
  -e HELLO_API_SITE_ADDRESS=http://api.localhost:80 \
  -e HELLO_WEB_SITE_ADDRESS=http://myapp.localhost:80 \
  -e GROCY_SITE_ADDRESS=http://grocy.localhost:80 \
  -v "$PWD/gateway/Caddyfile:/etc/caddy/Caddyfile:ro,Z" \
  -v "$PWD/gateway/conf.d:/etc/caddy/conf.d:ro,Z" \
  docker.io/library/caddy:2-alpine \
  caddy validate --config /etc/caddy/Caddyfile
```

Check the shared network:

```sh
podman network inspect caddy-public
```

Check name resolution between containers by running a temporary container on the network:

```sh
podman run --rm --network caddy-public docker.io/library/alpine:latest nslookup caddy-static
```

Test local gateway routing with host headers:

```sh
curl -i -H 'Host: myapp.localhost' http://127.0.0.1:8080
curl -i -H 'Host: grocy.localhost' http://127.0.0.1:8080
```

Common failure checks:

- DNS points each public hostname at the server.
- Firewall allows public ports `80` and `443`.
- No other process owns ports `80` or `443`.
- Containers are attached to `caddy-public`.
- Caddy route upstream names match container names.
- Runtime files exist under `~/selfhosted/...` paths referenced by Quadlets.
- The server clock is correct for TLS certificate validation.

## Backups

Back up persistent runtime data, not generated containers:

- `~/selfhosted/gateway/data`
- `~/selfhosted/gateway/config`
- `~/selfhosted/services/*/config`
- Any service-specific database or upload directories documented in `services/<name>/README.md`

The Hello App example stores no persistent runtime data in this infrastructure repo.
