# Caddy Gateway With FastAPI, Podman Quadlets, And Compose

This project runs a shared Caddy gateway plus a small FastAPI backend.

Caddy serves a static HTML page and reverse proxies API traffic to the backend. The services are intentionally independent: Caddy is the reusable edge/gateway service, and each app can join the shared `caddy-public` Podman network and add its own Caddy drop-in config.

## Recommended Layout

For this tutorial, a single repository is the best layout because it keeps the gateway, one example backend, Quadlets, and Compose files together:

- `Caddyfile`: base shared Caddy config.
- `caddy.env`: Caddy hostnames for local or production.
- `conf.d/`: Caddy drop-in site configs for apps.
- `site/`: static HTML served by Caddy.
- `apps/hello-api/`: FastAPI backend managed with `uv` and `pyproject.toml`.
- `quadlet/`: systemd Quadlets for Podman deployment.
- `compose.yml`: local Compose stack.
- `compose.production.yml`: production-style Compose stack using ports `80` and `443`.
- `data/` and `config/`: persistent Caddy runtime state and certificates.

For larger production use, split this into one gateway/deployment repo plus separate app repos. Keep the shared Caddy service independent, and let each app provide its own container image plus `conf.d/<app>.caddy` reverse-proxy file.

## Hostnames

Local defaults in `caddy.env`:

```sh
SITE_ADDRESS=http://localhost:80
API_SITE_ADDRESS=http://api.localhost:80
```

With the local Quadlet or local Compose file, container port `80` is published as `127.0.0.1:8080`, so test URLs are:

- Static site: `http://localhost:8080`
- API through Caddy: `http://api.localhost:8080/api/hello`

Production example:

```sh
SITE_ADDRESS=hello.myhostname.com
API_SITE_ADDRESS=api.myhostname.com
```

Caddy automatically requests and renews TLS certificates for real public hostnames when DNS points to the server and ports `80` and `443` are reachable.

## FastAPI Development With uv

Install `uv` if needed:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Run the API directly during development:

```sh
cd apps/hello-api
uv sync
uv run uvicorn hello_api.main:app --reload
```

Test the API directly:

```sh
curl http://localhost:8000/api/hello
curl http://localhost:8000/api/health
```

Run tests:

```sh
cd apps/hello-api
uv run pytest
```

Lock dependencies for repeatable builds:

```sh
cd apps/hello-api
uv lock
```

## Local Stack With Compose

Use this for the fastest local full-stack test.

Start the stack with Podman Compose:

```sh
podman compose up --build
```

If you use Docker Compose instead:

```sh
docker compose up --build
```

Test through Caddy:

```sh
curl -i http://localhost:8080
curl -i http://api.localhost:8080/api/hello
curl -i http://api.localhost:8080/api/health
```

If your system does not resolve `api.localhost`, send the host header manually:

```sh
curl -i -H 'Host: api.localhost' http://127.0.0.1:8080/api/hello
```

Stop the stack:

```sh
podman compose down
```

## Local Stack With Quadlets

The Quadlet setup uses rootless Podman and systemd user services.

1. Copy gateway files to the runtime path used by the Quadlets:

```sh
mkdir -p ~/caddy-static
cp -a Caddyfile caddy.env conf.d site data config ~/caddy-static/
```

2. Build the backend image:

```sh
podman build -t localhost/hello-api:latest -f apps/hello-api/Containerfile apps/hello-api
```

3. Install the shared network, backend, and local Caddy Quadlets:

```sh
mkdir -p ~/.config/containers/systemd
cp quadlet/caddy-public.network ~/.config/containers/systemd/
cp quadlet/hello-api.container ~/.config/containers/systemd/
cp quadlet/caddy-local.container ~/.config/containers/systemd/caddy-static.container
systemctl --user daemon-reload
```

4. Start services:

```sh
systemctl --user start hello-api.service caddy-static.service
```

5. Test:

```sh
curl -i http://localhost:8080
curl -i http://api.localhost:8080/api/hello
```

6. Enable services on boot:

```sh
systemctl --user enable hello-api.service caddy-static.service
loginctl enable-linger "$USER"
```

Check logs:

```sh
journalctl --user -u hello-api.service -f
journalctl --user -u caddy-static.service -f
```

## Production With Quadlets

Use this when you have a real server and DNS names such as `hello.myhostname.com` and `api.myhostname.com`.

1. Point DNS to your server:

- Create an `A` record for `hello.myhostname.com`.
- Create an `A` record for `api.myhostname.com`.
- Create `AAAA` records too if the server has IPv6.

2. Deploy gateway files:

```sh
mkdir -p ~/caddy-static
cp -a Caddyfile caddy.env conf.d site data config ~/caddy-static/
```

3. Edit production hostnames:

```sh
nano ~/caddy-static/caddy.env
```

Example:

```sh
SITE_ADDRESS=hello.myhostname.com
API_SITE_ADDRESS=api.myhostname.com
```

4. Build or pull the backend image:

```sh
podman build -t localhost/hello-api:latest -f apps/hello-api/Containerfile apps/hello-api
```

5. Install production Quadlets:

```sh
mkdir -p ~/.config/containers/systemd
cp quadlet/caddy-public.network ~/.config/containers/systemd/
cp quadlet/hello-api.container ~/.config/containers/systemd/
cp quadlet/caddy-production.container ~/.config/containers/systemd/caddy-static.container
systemctl --user daemon-reload
```

6. Allow rootless Podman to bind ports `80` and `443` if needed:

```sh
sudo sysctl net.ipv4.ip_unprivileged_port_start=80
```

Make it persistent:

```sh
printf 'net.ipv4.ip_unprivileged_port_start=80\n' | sudo tee /etc/sysctl.d/99-rootless-podman-low-ports.conf
sudo sysctl --system
```

7. Open firewall ports:

```sh
sudo firewall-cmd --add-service=http --add-service=https --permanent
sudo firewall-cmd --reload
```

If you do not use firewalld, open inbound TCP `80`, TCP `443`, and optionally UDP `443` with your firewall or cloud security group.

8. Start and enable services:

```sh
systemctl --user start hello-api.service caddy-static.service
systemctl --user enable hello-api.service caddy-static.service
loginctl enable-linger "$USER"
```

9. Test from another machine:

```sh
curl -I https://hello.myhostname.com
curl -i https://api.myhostname.com/api/hello
```

## Production-Style Compose

Compose is useful for testing the same topology without systemd Quadlets.

Edit `caddy.env` for production hostnames, then run:

```sh
podman compose -f compose.production.yml up --build -d
```

Stop it:

```sh
podman compose -f compose.production.yml down
```

## Adding Another App

1. Build or pull the app container image.
2. Attach the app container to the `caddy-public` network.
3. Add a Caddy drop-in under `conf.d/`, for example `conf.d/my-app.caddy`:

```caddyfile
my-app.myhostname.com {
	encode zstd gzip
	reverse_proxy my-app-container:3000
}
```

4. Restart Caddy:

```sh
systemctl --user restart caddy-static.service
```

Each app should use a unique hostname unless you intentionally route by path in a single shared site block.

## Updating The Static Page

Edit:

```sh
nano ~/caddy-static/site/index.html
```

No restart is needed for normal static file changes.

## Rebuilding The Backend

After changing backend code:

```sh
podman build -t localhost/hello-api:latest -f apps/hello-api/Containerfile apps/hello-api
systemctl --user restart hello-api.service
```

With Compose:

```sh
podman compose up --build -d
```

## Troubleshooting

List services:

```sh
systemctl --user list-units '*caddy*' '*hello-api*'
```

Check service logs:

```sh
journalctl --user -u caddy-static.service -f
journalctl --user -u hello-api.service -f
```

Check container logs:

```sh
podman logs caddy-static
podman logs hello-api
```

Check the shared network:

```sh
podman network inspect caddy-public
```

Reload after changing Quadlet files:

```sh
systemctl --user daemon-reload
systemctl --user restart hello-api.service caddy-static.service
```

If production TLS fails, verify:

- DNS points to this server for every configured hostname.
- Ports `80` and `443` are reachable from the internet.
- No other process is already using ports `80` or `443`.
- The server clock is correct.
