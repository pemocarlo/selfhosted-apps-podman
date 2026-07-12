# Grocy

LinuxServer.io Grocy household inventory app. Use root [README](../../README.md) and [operations docs](../../docs/operations.md).

## Files

- `quadlet/grocy.container`: app container.
- `grocy.env.example`: `PUID`, `PGID`, and `TZ` defaults.
- `config/`: persistent Grocy application data.
- `../../gateway/conf.d/grocy.caddy`: public route.

## Example Lines

```sh
PUID=1000
PGID=1000
TZ=Etc/UTC
GROCY_SITE_ADDRESS=grocy.example.com
```

```caddyfile
{$GROCY_SITE_ADDRESS:http://grocy.localhost:80} {
	reverse_proxy grocy:80
}
```

## Deploy

Review generated `~/selfhosted/services/grocy/grocy.env` for `PUID`, `PGID`, and `TZ`. Set `GROCY_SITE_ADDRESS` in `~/selfhosted/gateway/caddy.env`.

```sh
scripts/selfhosted deploy app grocy
scripts/selfhosted update grocy
scripts/selfhosted disable grocy
```

## Notes

- `config/` is the only persistent app data path.
- `grocy.env.example` is the only service env template.
- Back up `~/selfhosted/services/grocy/config`.
