# Operations

Manual deployment and troubleshooting live here. Root [README](../README.md) keeps automated flow and repo layout only.

## Manual Install

Gateway:

```sh
mkdir -p ~/selfhosted/gateway/{conf.d,site,data,config} ~/.config/containers/systemd
cp gateway/Caddyfile ~/selfhosted/gateway/
cp -a gateway/conf.d/. ~/selfhosted/gateway/conf.d/
cp -a gateway/site/. ~/selfhosted/gateway/site/
cp gateway/caddy.env.example ~/selfhosted/gateway/caddy.env
cp gateway/quadlet/caddy-public.network ~/.config/containers/systemd/
cp gateway/quadlet/caddy-production.container ~/.config/containers/systemd/caddy-static.container
systemctl --user daemon-reload
systemctl --user restart caddy-static.service
```

Gateway local test:

```sh
cp gateway/quadlet/caddy-local.container ~/.config/containers/systemd/caddy-static.container
systemctl --user daemon-reload
systemctl --user restart caddy-static.service
curl -i http://localhost:8080
```

App example:

```sh
mkdir -p ~/selfhosted/services/<name> ~/.config/containers/systemd
cp services/<name>/*.env.example ~/selfhosted/services/<name>/
cp services/<name>/quadlet/* ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user restart <unit>.service
systemctl --user try-restart caddy-static.service
```

Manual disable:

```sh
touch ~/selfhosted/services/<name>/.disabled
systemctl --user stop <unit>.service
rm -f ~/.config/containers/systemd/<name>*
systemctl --user daemon-reload
```

Do not delete runtime data. Do not run `systemctl --user enable` on generated Quadlet services.

## Troubleshooting

```sh
python3 -m py_compile scripts/selfhosted.py
bash -n scripts/selfhosted
git diff --check
uv run --script scripts/selfhosted.py status all
systemctl --user cat <unit>.service
journalctl --user -u <unit>.service -f
podman logs <container>
podman network inspect caddy-public
```

Check DNS, firewall, ports `80`/`443`, runtime env paths, Caddy upstream names, and server clock.

Validate Caddy:

```sh
podman run --rm \
  --env-file "$PWD/gateway/caddy.env.example" \
  -v "$PWD/gateway/Caddyfile:/etc/caddy/Caddyfile:ro,Z" \
  -v "$PWD/gateway/conf.d:/etc/caddy/conf.d:ro,Z" \
  docker.io/library/caddy:2-alpine \
  caddy validate --config /etc/caddy/Caddyfile
```

If Podman runtime access is blocked in your shell, run the same commands on the VPS user session instead.

## Maintenance

```sh
uv run --script scripts/selfhosted.py update <name>
uv run --script scripts/selfhosted.py update all
uv run --script scripts/selfhosted.py deploy app <name>
uv run --script scripts/selfhosted.py deploy gateway production
podman images
podman image prune
```

Pinned image tags require a Quadlet update. Floating tags pull latest image. Back up before upgrades or migrations.
