# Hello App

Deployment definition for the Hello App images built by the sibling `../hello-app` development repository.

This infrastructure repo does not contain the application source. It only contains the Podman Quadlets and Caddy routes needed to run the already-built images.

## Images

Default image names used by these Quadlets:

- `localhost/hello-api:latest`
- `localhost/hello-web:latest`

For a real production registry, edit the `Image=` lines in:

- `quadlet/hello-api.container`
- `quadlet/hello-web.container`

If you use registry images, change `AutoUpdate=local` to `AutoUpdate=registry`.

## Caddy Routes

Gateway routes live outside this service directory:

- `../../gateway/conf.d/hello-api.caddy`: optional direct API hostname, for example `api.myhostname.com`.
- `../../gateway/conf.d/hello-web.caddy`: frontend hostname, for example `myapp.myhostname.com`, with `/api/*` proxied to `hello-api`.

For most browser usage, expose only `HELLO_WEB_SITE_ADDRESS` publicly and let `/api/*` route through the frontend hostname.

## Deploy

Build or pull the images first. From the sibling `../hello-app` development repo, local builds are:

```sh
podman build -t localhost/hello-api:latest -f api/Containerfile api
podman build -t localhost/hello-web:latest -f web/Containerfile web
```

Then install the Quadlets from this infrastructure repo:

```sh
mkdir -p ~/.config/containers/systemd
cp services/hello-app/quadlet/hello-api.container ~/.config/containers/systemd/
cp services/hello-app/quadlet/hello-web.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user start hello-api.service hello-web.service
systemctl --user enable hello-api.service hello-web.service
systemctl --user restart caddy-static.service
```

## Test

Local gateway:

```sh
curl -i -H 'Host: myapp.localhost' http://127.0.0.1:8080
curl -i -H 'Host: myapp.localhost' http://127.0.0.1:8080/api/hello
```

Production:

```sh
curl -I https://myapp.myhostname.com
curl -i https://myapp.myhostname.com/api/hello
```

## Update

Build or pull newer images, then restart the services:

```sh
systemctl --user restart hello-api.service hello-web.service
```

If Caddy routes changed, restart the gateway too:

```sh
systemctl --user restart caddy-static.service
```

## Logs

```sh
journalctl --user -u hello-api.service -f
journalctl --user -u hello-web.service -f
podman logs hello-api
podman logs hello-web
```
