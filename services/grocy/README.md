# Grocy

LinuxServer.io Grocy household inventory app. Use root [README](../../README.md) and [operations docs](../../docs/operations.md).

## Files

- `quadlet/grocy.container`: app container.
- `grocy.example.env`: `PUID`, `PGID`, and `TZ` defaults.
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

Review generated `~/selfhosted/services/grocy/grocy.env` for `PUID`, `PGID`, and `TZ`. Run `id -u` and `id -g` to find the deployment user's values. Set `GROCY_SITE_ADDRESS` in `~/selfhosted/gateway/caddy.env`.

```sh
scripts/selfhosted deploy grocy
scripts/selfhosted update grocy
scripts/selfhosted disable grocy
```

Sign in with Grocy's initial `admin` / `admin` credentials and change the password immediately.

## Notes

- `config/` is the only persistent app data path.
- `grocy.example.env` is the only service env template.
- After an image update, open Grocy's root page once so any pending database migrations run.
- Back up `~/selfhosted/services/grocy/config`.
