# Hello App

Example frontend/API deployment. The application source and image builds live
in a separate repository; this directory only demonstrates how two local
images can be wired into Quadlets and Caddy.

## Images and routes

Build or load these images on the VPS before deployment:

- `localhost/hello-api:latest`
- `localhost/hello-web:latest`

The web route serves the frontend and proxies `/api/*` to `hello-api`. An
optional separate API hostname is defined in `gateway/conf.d/hello-api.caddy`.
Set `HELLO_WEB_SITE_ADDRESS` and, if needed, `HELLO_API_SITE_ADDRESS` in the
gateway env file, then deploy the gateway.

## Deploy and lifecycle

```sh
podman image exists localhost/hello-api:latest
podman image exists localhost/hello-web:latest
scripts/selfhosted deploy hello-app
scripts/selfhosted status hello-app
scripts/selfhosted logs hello-app --follow
scripts/selfhosted restart hello-app
```

Because these are local images, `scripts/selfhosted update hello-app` does not
pull from a registry. Rebuild and retag both images, then run the update or
restart command. This example has no persistent data paths; add them to the
Quadlets and service README before using it as a real application template.

## Further reading

- [Podman Quadlet documentation](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)
- [Caddy reverse proxy directive](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
- [Adding a service in this repository](../../docs/adding-a-service.md)
- [Manual lifecycle commands](../../docs/manual.md)
