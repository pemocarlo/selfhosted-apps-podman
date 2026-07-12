# Hello App

Example frontend/API deployment. Application source and image builds live in a separate repository. Use root [README](../../README.md) and [operations docs](../../docs/operations.md).

## Files

- `quadlet/hello-api.container`: API container.
- `quadlet/hello-web.container`: frontend container.
- `../../gateway/conf.d/hello-api.caddy`: optional direct API hostname.
- `../../gateway/conf.d/hello-web.caddy`: frontend hostname and `/api/*` proxy.

## Example Lines

```sh
HELLO_WEB_SITE_ADDRESS=myapp.example.com
HELLO_API_SITE_ADDRESS=api.example.com
```

```caddyfile
{$HELLO_WEB_SITE_ADDRESS:http://myapp.localhost:80} {
	handle /api/* {
		reverse_proxy hello-api:8000
	}
	handle {
		reverse_proxy hello-web:8080
	}
}
```

## Images

Current Quadlets use local images:

- `localhost/hello-api:latest`
- `localhost/hello-web:latest`

Build them on VPS before deploy, or change `Image=` to registry references and `AutoUpdate=registry`.

## Commands

```sh
scripts/selfhosted deploy hello-app
scripts/selfhosted update hello-app
scripts/selfhosted disable hello-app
```

## Notes

- `hello-web` proxies `/api/*` to `hello-api`.
- Set `HELLO_WEB_SITE_ADDRESS` and optional `HELLO_API_SITE_ADDRESS` in `~/selfhosted/gateway/caddy.env`.
- Service-specific test commands live in `docs/operations.md`.
