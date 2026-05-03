# Grocy

Grocy is a household inventory and recipe management app.

This service uses the LinuxServer.io Grocy image and is exposed through the shared Caddy gateway.

## Files

- `quadlet/grocy.container`: production Podman Quadlet.
- `grocy.env.example`: environment template.
- `config/`: persistent Grocy app data.
- `../../gateway/conf.d/grocy.caddy`: Caddy reverse-proxy route.

## Deploy

From the repository root on the server:

```sh
mkdir -p ~/selfhosted/services/grocy
cp -a services/grocy/config ~/selfhosted/services/grocy/
cp services/grocy/grocy.env.example ~/selfhosted/services/grocy/grocy.env
```

Edit user/group IDs and timezone if needed:

```sh
nano ~/selfhosted/services/grocy/grocy.env
```

Install the Quadlet:

```sh
mkdir -p ~/.config/containers/systemd
cp services/grocy/quadlet/grocy.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start grocy.service
```

Do not run `systemctl --user enable grocy.service`; Quadlet services are generated. Autostart is controlled by `[Install] WantedBy=default.target` in `grocy.container`.

Make sure the gateway has `gateway/conf.d/grocy.caddy` deployed and that `GROCY_SITE_ADDRESS` is set in `~/selfhosted/gateway/caddy.env`.

Restart Caddy after adding the route:

```sh
systemctl --user restart caddy-static.service
```

## Test

Local Quadlet gateway:

```sh
curl -I -H 'Host: grocy.localhost' http://127.0.0.1:8080
```

Production:

```sh
curl -I https://grocy.myhostname.com
```

## Data

Grocy state is stored in:

```text
~/selfhosted/services/grocy/config
```

Back up this directory before upgrades or server migrations.
