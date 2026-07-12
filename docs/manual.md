# Manual installation

Run these commands from the repository root as the rootless deployment user.

## Gateway

Create runtime directories and copy configuration. The existence check preserves an existing env file.

```sh
install -d ~/selfhosted/gateway/{conf.d,site,data,config} ~/.config/containers/systemd
install -m 0644 gateway/Caddyfile ~/selfhosted/gateway/Caddyfile
cp -a gateway/conf.d/. ~/selfhosted/gateway/conf.d/
cp -a gateway/site/. ~/selfhosted/gateway/site/
test -e ~/selfhosted/gateway/caddy.env || \
  install -m 0600 gateway/caddy.env.example ~/selfhosted/gateway/caddy.env
nano ~/selfhosted/gateway/caddy.env

install -m 0644 gateway/quadlet/caddy-public.network ~/.config/containers/systemd/
install -m 0644 gateway/quadlet/caddy-local.container \
  ~/.config/containers/systemd/caddy-static.container
systemctl --user daemon-reload
systemctl --user restart caddy-static.service
curl -I http://localhost:8080
```

For production, ensure DNS and firewall configuration are ready, then replace only the gateway definition:

```sh
install -m 0644 gateway/quadlet/caddy-production.container \
  ~/.config/containers/systemd/caddy-static.container
systemctl --user daemon-reload
systemctl --user restart caddy-static.service
```

## One app

Grocy example:

```sh
install -d ~/selfhosted/services/grocy/config ~/.config/containers/systemd
test -e ~/selfhosted/services/grocy/grocy.env || \
  install -m 0600 services/grocy/grocy.env.example ~/selfhosted/services/grocy/grocy.env
install -m 0644 services/grocy/quadlet/* ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user restart grocy.service
```

For BookStack, create its `mysql`, `public-uploads`, and `storage-uploads` directories; copy both env templates without overwriting existing files; replace every `CHANGE_ME`; then install all files from `services/bookstack/quadlet/`. Service READMEs list the exact settings and data paths.

## Lifecycle commands

```sh
systemctl --user status grocy.service
journalctl --user -u grocy.service -f
podman logs grocy

podman pull lscr.io/linuxserver/grocy:latest
systemctl --user restart grocy.service

systemctl --user stop grocy.service
rm ~/.config/containers/systemd/grocy.container
systemctl --user daemon-reload
```

Removing a Quadlet definition does not remove its container data. Never delete `~/selfhosted/services/<name>` during deploy or disable operations.

To apply configuration changes, copy the changed files and Quadlets, reload systemd, and restart only the affected service.
