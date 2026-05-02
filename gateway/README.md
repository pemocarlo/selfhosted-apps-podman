# Gateway

The gateway is the shared Caddy edge service. It is intentionally independent from the apps it exposes.

Apps join the `caddy-public` Podman network and add one Caddy drop-in file under `gateway/conf.d/`.

## Files

- `Caddyfile`: base Caddy config.
- `caddy.env.example`: hostname template. Copy this to `caddy.env` on the server.
- `conf.d/*.caddy`: app routes loaded by Caddy.
- `site/`: static landing page.
- `quadlet/caddy-public.network`: shared Podman network.
- `quadlet/caddy-local.container`: local gateway on `127.0.0.1:8080`.
- `quadlet/caddy-production.container`: production gateway on `80`, `443/tcp`, and `443/udp`.
- `data/`: Caddy certificate and storage data.
- `config/`: Caddy runtime config.

## Deploy Locally

```sh
mkdir -p ~/selfhosted/gateway
cp -a gateway/Caddyfile gateway/conf.d gateway/site gateway/data gateway/config ~/selfhosted/gateway/
cp gateway/caddy.env.example ~/selfhosted/gateway/caddy.env
mkdir -p ~/.config/containers/systemd
cp gateway/quadlet/caddy-public.network ~/.config/containers/systemd/
cp gateway/quadlet/caddy-local.container ~/.config/containers/systemd/caddy-static.container
systemctl --user daemon-reload
systemctl --user start caddy-static.service
```

Test:

```sh
curl -i http://localhost:8080
```

## Deploy In Production

```sh
mkdir -p ~/selfhosted/gateway
cp -a gateway/Caddyfile gateway/conf.d gateway/site gateway/data gateway/config ~/selfhosted/gateway/
cp gateway/caddy.env.example ~/selfhosted/gateway/caddy.env
nano ~/selfhosted/gateway/caddy.env
mkdir -p ~/.config/containers/systemd
cp gateway/quadlet/caddy-public.network ~/.config/containers/systemd/
cp gateway/quadlet/caddy-production.container ~/.config/containers/systemd/caddy-static.container
systemctl --user daemon-reload
systemctl --user start caddy-static.service
systemctl --user enable caddy-static.service
loginctl enable-linger "$USER"
```

## Port 80 In Production

You do not strictly need port `80`, but it is the simplest and most reliable setup for public HTTPS with Caddy.

Recommended setup:

- Open TCP `80` so Caddy can complete ACME HTTP-01 certificate challenges.
- Open TCP `443` for HTTPS traffic.
- Open UDP `443` for HTTP/3.
- Let Caddy redirect HTTP to HTTPS automatically.

Alternatives if you cannot expose TCP `80`:

- Use ACME TLS-ALPN-01, which works on TCP `443`, but some environments and firewalls make this less convenient.
- Use DNS-01 challenges with a Caddy build that includes your DNS provider module.
- Use an internal/private CA if this is not internet-facing.

For normal public self-hosting, keep TCP `80` open.

## Add A Route

Add a file such as `gateway/conf.d/my-app.caddy`:

```caddyfile
my-app.example.com {
	encode zstd gzip
	reverse_proxy my-app:3000
}
```

Restart the gateway after deploying the file:

```sh
systemctl --user restart caddy-static.service
```
