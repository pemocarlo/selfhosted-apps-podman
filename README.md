# Selfhosted Apps With Podman Quadlets

This repository is organized like a small self-hosted app catalog. The shared Caddy gateway lives in `gateway/`, and each app lives in `services/<name>/` with its own README, Quadlet, persistent data, and Caddy route.

The production runtime is Podman + systemd Quadlets. Compose is included only for development of the React + FastAPI example.

## Layout

- `gateway/`: shared Caddy reverse proxy, TLS, static landing page, and shared Podman network.
- `services/hello-api/`: FastAPI backend managed by `uv`.
- `services/hello-web/`: minimal React app that calls the Python API. Development only.
- `services/grocy/`: Grocy household ERP service.
- `compose.dev.yml`: development stack for `hello-web` + `hello-api`.

## Services

| Service | Public Host Example | Role | Deployment |
| --- | --- | --- | --- |
| Gateway | `hello.myhostname.com` | Caddy edge, TLS, static landing page | Quadlet |
| Hello API | `api.myhostname.com` | FastAPI backend | Quadlet |
| Hello Web | `localhost:5173` | React development UI | Compose dev only |
| Grocy | `grocy.myhostname.com` | Household inventory app | Quadlet |

## Production Model

The gateway is independent because many apps can use it. Every production app should:

- Run as its own Podman container or pod.
- Join the shared `caddy-public` network.
- Store persistent data under `~/selfhosted/services/<name>/`.
- Add one route under `~/selfhosted/gateway/conf.d/<name>.caddy`.
- Have its own `services/<name>/README.md` with deploy, update, backup, and test notes.

This keeps Caddy stable while apps can be added, restarted, upgraded, or removed independently.

## Initial Server Setup

Install Podman with Quadlet support and make sure user services work:

```sh
podman --version
systemctl --user status
```

Enable user services to keep running after logout:

```sh
loginctl enable-linger "$USER"
```

Create the runtime root:

```sh
mkdir -p ~/selfhosted
```

## Deploy Gateway

Copy gateway files:

```sh
mkdir -p ~/selfhosted/gateway
cp -a gateway/Caddyfile gateway/conf.d gateway/site gateway/data gateway/config ~/selfhosted/gateway/
cp gateway/caddy.env.example ~/selfhosted/gateway/caddy.env
```

Edit hostnames:

```sh
nano ~/selfhosted/gateway/caddy.env
```

Local defaults:

```sh
SITE_ADDRESS=http://localhost:80
HELLO_API_SITE_ADDRESS=http://api.localhost:80
GROCY_SITE_ADDRESS=http://grocy.localhost:80
```

Production example:

```sh
SITE_ADDRESS=hello.myhostname.com
HELLO_API_SITE_ADDRESS=api.myhostname.com
GROCY_SITE_ADDRESS=grocy.myhostname.com
```

Install local gateway Quadlets:

```sh
mkdir -p ~/.config/containers/systemd
cp gateway/quadlet/caddy-public.network ~/.config/containers/systemd/
cp gateway/quadlet/caddy-local.container ~/.config/containers/systemd/caddy-static.container
systemctl --user daemon-reload
systemctl --user start caddy-static.service
```

For production, use the production gateway unit instead:

```sh
cp gateway/quadlet/caddy-production.container ~/.config/containers/systemd/caddy-static.container
systemctl --user daemon-reload
systemctl --user restart caddy-static.service
systemctl --user enable caddy-static.service
```

## Do We Need Port 80?

Not strictly, but yes for the recommended production setup.

Caddy can manage public certificates most reliably when TCP `80` and TCP `443` are reachable. Port `80` is used for ACME HTTP-01 certificate challenges and for redirecting plain HTTP to HTTPS. Port `443` serves HTTPS. UDP `443` enables HTTP/3.

If you cannot expose TCP `80`, options are:

- Use TLS-ALPN-01 on TCP `443`; this can work but removes the normal HTTP redirect path.
- Use DNS-01 with a custom Caddy image containing your DNS provider plugin.
- Use private/internal certificates if the service is not public.

For a normal public VPS, open TCP `80`, TCP `443`, and optionally UDP `443`.

For rootless Podman low ports, allow binding below `1024`:

```sh
sudo sysctl net.ipv4.ip_unprivileged_port_start=80
printf 'net.ipv4.ip_unprivileged_port_start=80\n' | sudo tee /etc/sysctl.d/99-rootless-podman-low-ports.conf
sudo sysctl --system
```

Open firewall ports if you use firewalld:

```sh
sudo firewall-cmd --add-service=http --add-service=https --permanent
sudo firewall-cmd --reload
```

## Deploy Hello API

Build the image:

```sh
podman build -t localhost/hello-api:latest -f services/hello-api/Containerfile services/hello-api
```

Install and start the service:

```sh
cp services/hello-api/quadlet/hello-api.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start hello-api.service
systemctl --user enable hello-api.service
systemctl --user restart caddy-static.service
```

Test locally through Caddy:

```sh
curl -i -H 'Host: api.localhost' http://127.0.0.1:8080/api/hello
```

More details: `services/hello-api/README.md`.

## Deploy Grocy

Copy persistent config and environment:

```sh
mkdir -p ~/selfhosted/services/grocy
cp -a services/grocy/config ~/selfhosted/services/grocy/
cp services/grocy/grocy.env.example ~/selfhosted/services/grocy/grocy.env
nano ~/selfhosted/services/grocy/grocy.env
```

Install and start:

```sh
cp services/grocy/quadlet/grocy.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start grocy.service
systemctl --user enable grocy.service
systemctl --user restart caddy-static.service
```

Test locally through Caddy:

```sh
curl -I -H 'Host: grocy.localhost' http://127.0.0.1:8080
```

More details: `services/grocy/README.md`.

## Development: React + FastAPI

The development Compose file runs only the React app and Python API. It does not deploy Grocy or the production gateway.

Start:

```sh
systemctl --user start podman.socket
podman compose -f compose.dev.yml up --build
```

Open:

```text
http://localhost:5173
```

Test the API directly:

```sh
curl http://localhost:8000/api/hello
```

Stop:

```sh
podman compose -f compose.dev.yml down
```

If `podman compose` reports a missing `/run/user/.../podman.sock`, start the socket with `systemctl --user start podman.socket` and try again.

More details: `services/hello-web/README.md`.

## Add A New Service

1. Create a directory: `services/my-service/`.
2. Add `services/my-service/README.md` with deploy, update, backup, and test steps.
3. Add persistent directories such as `services/my-service/config/.gitkeep` if needed.
4. Add an environment template such as `services/my-service/my-service.env.example` if needed.
5. Add a Quadlet at `services/my-service/quadlet/my-service.container`.
6. Attach the Quadlet to `Network=caddy-public.network`.
7. Add a route at `gateway/conf.d/my-service.caddy`.
8. Add a hostname variable to `gateway/caddy.env.example` if the route should be environment-driven.
9. Deploy service files to `~/selfhosted/services/my-service/`.
10. Copy the Quadlet to `~/.config/containers/systemd/`, reload systemd, start the service, and restart Caddy.

Minimal Quadlet example:

```ini
[Unit]
Description=My Service

[Container]
Image=example/my-service:latest
ContainerName=my-service
Network=caddy-public.network
Volume=%h/selfhosted/services/my-service/config:/config:Z

[Service]
Restart=always

[Install]
WantedBy=default.target
```

Minimal Caddy route:

```caddyfile
{$MY_SERVICE_SITE_ADDRESS:my-service.example.com} {
	encode zstd gzip
	reverse_proxy my-service:3000
}
```

## Operations

List services:

```sh
systemctl --user list-units '*caddy*' '*hello-api*' '*grocy*'
```

Check logs:

```sh
journalctl --user -u caddy-static.service -f
journalctl --user -u hello-api.service -f
journalctl --user -u grocy.service -f
```

Check containers:

```sh
podman ps
podman logs caddy-static
podman logs hello-api
podman logs grocy
```

Reload Quadlet changes:

```sh
systemctl --user daemon-reload
systemctl --user restart caddy-static.service
```

Inspect shared network:

```sh
podman network inspect caddy-public
```

## Backups

Back up at least these runtime directories:

- `~/selfhosted/gateway/data`
- `~/selfhosted/gateway/config`
- `~/selfhosted/services/grocy/config`

The `hello-api` example has no persistent runtime data.
