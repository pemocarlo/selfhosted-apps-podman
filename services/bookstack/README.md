# BookStack

BookStack wiki plus private MySQL container. Use root [README](../../README.md) and [operations docs](../../docs/operations.md).

## Files

- `quadlet/bookstack.container`: app container.
- `quadlet/bookstack-db.container`: MySQL container.
- `quadlet/bookstack-internal.network`: private app-to-db network.
- `bookstack.env.example`: app settings, URL, and secret placeholders.
- `bookstack-db.env.example`: database name and credentials.
- `mysql/`: persistent database data.
- `public-uploads/`: public uploads.
- `storage-uploads/`: private uploads.
- `../../gateway/conf.d/bookstack.caddy`: public route.

## Example Lines

```sh
APP_URL=https://bookstack.example.com
DB_PASSWORD=CHANGE_ME_DATABASE_PASSWORD
MYSQL_PASSWORD=CHANGE_ME_DATABASE_PASSWORD
BOOKSTACK_SITE_ADDRESS=bookstack.example.com
```

```caddyfile
{$BOOKSTACK_SITE_ADDRESS:http://bookstack.localhost:80} {
	reverse_proxy bookstack:8080
}
```

## Deploy

Before deploy, set matching `DB_PASSWORD` and `MYSQL_PASSWORD`, unique `APP_KEY`, and exact public `APP_URL` in generated runtime env files. `scripts/selfhosted deploy app bookstack` creates missing env files, then stops if placeholders remain.

```sh
openssl rand -base64 32
nano ~/selfhosted/services/bookstack/bookstack.env
nano ~/selfhosted/services/bookstack/bookstack-db.env
scripts/selfhosted deploy app bookstack
```

Set `BOOKSTACK_SITE_ADDRESS` in `~/selfhosted/gateway/caddy.env`. Change default login `admin@admin.com / password` immediately.

## Notes

- `bookstack.container` depends on `bookstack-db.container`.
- `bookstack-internal.network` keeps database traffic private.
- `bookstack-db.env.example` holds DB name and password vars.
- `bookstack.env.example` holds app URL, app key, and DB host/user vars.
- `mysql/`, `public-uploads/`, and `storage-uploads/` are persistent data paths.
- Backups, checks, and manual install live in `docs/operations.md`.
