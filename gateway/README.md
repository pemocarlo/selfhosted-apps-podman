# Gateway

Shared Caddy edge service. Deploy and operate it using root [README](../README.md) and [operations docs](../docs/operations.md).

## Files

- `Caddyfile`: base config and drop-in import.
- `caddy.env.example`: local hostname defaults and production examples.
- `conf.d/*.caddy`: app routes.
- `quadlet/caddy-local.container`: local gateway on `127.0.0.1:8080`.
- `quadlet/caddy-production.container`: production gateway on ports `80` and `443`.
- `quadlet/caddy-public.network`: shared network for exposed apps.
- `data/`: Caddy certs and storage.
- `config/`: Caddy runtime config.

## Example Lines

```sh
SITE_ADDRESS=http://localhost:80
BOOKSTACK_SITE_ADDRESS=http://bookstack.localhost:80
```

```caddyfile
{$BOOKSTACK_SITE_ADDRESS:http://bookstack.localhost:80} {
	reverse_proxy bookstack:8080
}
```

## Commands

```sh
uv run --script scripts/selfhosted.py deploy gateway local
uv run --script scripts/selfhosted.py deploy gateway production
uv run --script scripts/selfhosted.py update gateway
```

Add route hostname to deployed `~/selfhosted/gateway/caddy.env`, then redeploy gateway. See `docs/operations.md` for manual install, validation, and troubleshooting.
